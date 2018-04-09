import unittest

from unittest.mock import MagicMock, patch

from core import navigation
from core.point import Point
from core.way import Way
class NavigationTests(unittest.TestCase):

    # Turn
    def turn_base_test(self):
        """Test the Turn class."""
        session_mock = MagicMock()
        master_event_mock = MagicMock()

        point = Point(lat=1.0, lon=1.0)

        turn = navigation.Turn(session_mock, point, master_event_mock)

        # basic properties
        self.assertEqual(turn.session, session_mock)
        self.assertEqual(turn.point, point)

        # we have not added any events yet
        self.assertListEqual(turn.events, [])

        # add some mocked events
        mock_event_1 = MagicMock()
        mock_event_2 = MagicMock()
        turn.add_event(mock_event_1)
        turn.add_event(mock_event_2)

        # check the events have been added
        self.assertListEqual(turn.events, [mock_event_1, mock_event_2])

        # check prepare works (without doing anything)
        turn.prepare()

        # check check_events works (without doing anything)
        turn.check_events()

        # cleanup should also work, but yet again, it doesn't do anything
        # thanks to the power of magic mock
        turn.cleanup()

    # Trigger
    def trigger_base_test(self):
        """Test the Trigger base class."""
        trigger = navigation.Trigger()
        self.assertIsNone(trigger.event)
        self.assertFalse(trigger.triggered)
        with self.assertRaises(NotImplementedError):
            # Trigger is a basel class, so _do_check_condition(),
            # which is called by check_condition() raises NotImplementedError
            trigger.check_condition()
        self.assertFalse(trigger.triggered)
        # try setting some mock event, just in case
        mock_event = MagicMock()
        trigger.set_event(mock_event)
        self.assertEqual(trigger.event, mock_event)

    # DistanceTrigger
    def distance_trigger_test(self):
        """Test DistanceTrigger."""
        # create some points
        # - note that we are navigating in the Atlantic ocean
        #   south from the African coast :)
        starting_point = Point(lat=0.0, lon=0.0)
        mid_point = Point(lat=1.0, lon=0.0)
        target_point = Point(lat=2.0, lon=0.0)
        # mock the event, turn & session
        mock_event = MagicMock()
        mock_event.turn.point = target_point
        mock_event.turn.session.current_position = starting_point
        mock_event.turn.session.current_speed = 20

        # create the trigger
        trigger = navigation.DistanceTrigger(distance=30)
        trigger.set_event(mock_event)

        # first check - we should be long away from the destination
        self.assertFalse(trigger.check_condition())
        self.assertFalse(trigger.triggered)

        # second check - we should be midway but still far
        #                outside the trigger circle
        mock_event.turn.session.current_position = mid_point
        self.assertFalse(trigger.check_condition())
        self.assertFalse(trigger.triggered)

        # final check - the current position and the target point
        #               should be the same
        mock_event.turn.session.current_position = target_point
        self.assertTrue(trigger.check_condition())
        self.assertTrue(trigger.triggered)
        # check_condition() should return True only on when
        # the initial trigger fires

        # the trigger normally does not reset and will stay triggered
        # even after leaving the trigger circle
        mock_event.turn.session.current_position = mid_point
        self.assertFalse(trigger.check_condition())
        self.assertTrue(trigger.triggered)

        # even when we return to the condition being true,
        # check_condition() will still return False as
        # the trigger already fired once before
        mock_event.turn.session.current_position = target_point
        self.assertFalse(trigger.check_condition())
        self.assertTrue(trigger.triggered)

    def distance_trigger_fine_test(self):
        """"Test DistanceTrigger fine distance changes."""
        # create some points
        # - note that we are navigating in the Atlantic ocean
        #   south from the African coast :)
        far_outside_point = Point(lat=0.0, lon=0.0)
        slightly_outside_point = Point(lat=0.99, lon=0.0)
        inside_point = Point(lat=0.995, lon=0.0)
        target_point = Point(lat=1.0, lon=0.0)
        # mock the event, turn & session
        mock_event = MagicMock()
        mock_event.turn.point = target_point
        mock_event.turn.session.current_speed = 20

        # far outside - should not trigger
        mock_event.turn.session.current_position = far_outside_point
        trigger = navigation.DistanceTrigger(distance=1000)
        trigger.set_event(mock_event)
        self.assertFalse(trigger.check_condition())
        self.assertFalse(trigger.triggered)

        # slightly outside (~110 m outside) - still should not trigger
        mock_event.turn.session.current_position = slightly_outside_point
        trigger = navigation.DistanceTrigger(distance=1000)
        trigger.set_event(mock_event)
        self.assertFalse(trigger.check_condition())
        self.assertFalse(trigger.triggered)

        # inside the trigger circle (~560m from target point) - should trigger
        mock_event.turn.session.current_position = inside_point
        trigger = navigation.DistanceTrigger(distance=1000)
        trigger.set_event(mock_event)
        self.assertTrue(trigger.check_condition())
        self.assertTrue(trigger.triggered)

    def distance_trigger_fast_test(self):
        """"Test DistanceTrigger at high speed.

        The issue we are checking for here is simple:

        ModRana generally get's position updates once a second.
        If the speed in meters per second is bigger than the
        trigger circle, it is possible to "jump" over it in the
        time between two position updates.

        So what happens is that we check the speed in meters per second
        is > than 75% of the trigger distance and adjust the size
        of the trigger circle accordingly.

        Note that this is not exactly bullet proof,
        as it more or less breaks down if the update
        *does not* happen once per second, so some method
        of checking if a line between the current and
        previous position intersects the circle would
        work better.
        """

        # create some points
        # - note that we are navigating in the Atlantic ocean
        #   south from the African coast :)
        slightly_outside_point = Point(lat=0.99, lon=0.0)
        target_point = Point(lat=1.0, lon=0.0)
        # mock the event, turn & session
        mock_event = MagicMock()
        mock_event.turn.point = target_point
        # 1 km/s, whoo!
        mock_event.turn.session.current_speed = 1000

        # slightly outside (~110 m outside), but should trigger
        # as current speed in m/s > 75% of the trigger distance
        mock_event.turn.session.current_position = slightly_outside_point
        trigger = navigation.DistanceTrigger(distance=1000)
        trigger.set_event(mock_event)
        self.assertTrue(trigger.check_condition())
        self.assertTrue(trigger.triggered)

    # TimeToPointTrigger
    def time_to_point_trigger_test(self):
        """Test TimeToPointTrigger."""
        # create some points
        outside_point = Point(lat=0.99, lon=0.0)
        target_point = Point(lat=1.0, lon=0.0)
        # mock the event, turn & session
        mock_event = MagicMock()
        mock_event.turn.point = target_point
        mock_event.turn.session.average_speed = 42

        # we are about 1.11 km distant from the target
        # so it should takes us ~26 second to reach it at 42 m/s
        mock_event.turn.session.current_position = outside_point
        trigger = navigation.TimeToPointTrigger(time_to_point=30)
        trigger.set_event(mock_event)
        self.assertTrue(trigger.check_condition())
        self.assertTrue(trigger.triggered)

        # Also test that the trigger *does not* fire if we can't reach it
        # in time at current average speed.
        mock_event.turn.session.average_speed = 20
        trigger = navigation.TimeToPointTrigger(time_to_point=30)
        trigger.set_event(mock_event)
        self.assertFalse(trigger.check_condition())
        self.assertFalse(trigger.triggered)

    # Action
    def action_base_test(self):
        """Test the Action base class"""
        action = navigation.Action()
        # prepare is no-op by default
        action.prepare()
        with self.assertRaises(NotImplementedError):
            action.run()

    # NavigationEvent
    def navigation_event_test(self):
        """Test NavigationEvent."""

        mock_trigger = MagicMock()
        mock_turn = MagicMock()

        # check with no actions first
        event = navigation.NavigationEvent(trigger=mock_trigger,
                                           actions=[])
        event.set_turn(mock_turn)

        event.prepare()
        self.assertTrue(event.check_trigger())
        mock_trigger.check_condition.assert_called_once()
        event.cleanup()

        # now try with some actions
        mock_trigger = MagicMock()
        mock_trigger.check_condition.return_value = True
        mock_action1 = MagicMock()
        mock_action2 = MagicMock()
        mock_action3 = MagicMock()

        event = navigation.NavigationEvent(trigger=mock_trigger,
                                           actions=[mock_action1,
                                                    mock_action2,
                                                    mock_action3])
        event.set_turn(mock_turn)

        event.prepare()
        mock_action1.prepare.assert_called_once()
        mock_action2.prepare.assert_called_once()
        mock_action3.prepare.assert_called_once()

        self.assertTrue(event.check_trigger())
        mock_trigger.check_condition.assert_called_once()
        mock_action1.run.assert_called_once()
        mock_action2.run.assert_called_once()
        mock_action3.run.assert_called_once()

        # further check_condition() calls should not call run()
        # on actions
        mock_trigger.check_condition.return_value = False
        self.assertFalse(event.check_trigger())
        mock_action1.run.assert_called_once()
        mock_action2.run.assert_called_once()
        mock_action3.run.assert_called_once()

        event.cleanup()
        mock_action1.cleanup.assert_called_once()
        mock_action2.cleanup.assert_called_once()
        mock_action3.cleanup.assert_called_once()

    # Action
    def action_test(self):
        """Test the Action base class."""

        action = navigation.Action()
        action.prepare()
        with self.assertRaises(NotImplementedError):
            action.run()

    # VoiceMessage
    def voice_message_action_test(self):
        """Test the VoiceMessage action."""
        message = "Hello world!"
        filename = "/tmp/foo"
        mock_session = MagicMock()
        mock_session.voice_generator.get.return_value = filename
        voice_action = navigation.VoiceMessage(session=mock_session, message=message)
        voice_action.prepare()
        mock_session.voice_generator.make.assert_called_once_with(message)

        voice_action.run()
        mock_session.voice_generator.get.assert_called_once_with(message)
        mock_session.play_voice_sample.assert_called_once_with(filename)

        voice_action.clean()
        mock_session.voice_generator.clean_text.assert_called_once_with(message)

        # run() without prepare should not try to play the message
        mock_session = MagicMock()
        mock_session.voice_generator.get.return_value = None
        voice_action = navigation.VoiceMessage(session=mock_session, message=message)
        voice_action.run()
        mock_session.voice_generator.get.assert_called_once_with(message)
        mock_session.play_voice_sample.assert_not_called()

        # run() after clear() should also ot interact with the voice generator
        mock_session = MagicMock()
        mock_session.voice_generator.get.return_value = None
        voice_action = navigation.VoiceMessage(session=mock_session, message=message)
        voice_action.prepare()
        voice_action.clean()
        voice_action.run()
        mock_session.voice_generator.get.assert_not_called()
        mock_session.play_voice_sample.assert_not_called()

    # SwitchToNextTurn
    def switch_to_next_turn_action_test(self):
        """Test the SwitchToNextTurn action."""
        mock_session = MagicMock()
        switch_action = navigation.SwitchToNextTurn(session=mock_session)
        switch_action.run()
        mock_session.switch_to_next_turn.assert_called_once()

        # clean() should be basically a no-op
        switch_action.clean()

    # DestinationReached
    def destination_reached_test(self):
        """Test the DestinationReached action."""
        mock_session = MagicMock()
        destination_reached_action = navigation.DestinationReached(session=mock_session)
        destination_reached_action.run()
        mock_session.destination_reached.assert_called_once()

        # clean() should be basically a no-op
        destination_reached_action.clean()


    # AdjustedTimeDistance

    # NavigationManager

    # NavigationSession
    def navigation_session_basic_test(self):
        """Basic test of the NavigationSession class.

        Just check if Navigation session does not crash when created
        with mock inputs.
        """
        mock_manager = MagicMock()
        mock_voice_generator = MagicMock()
        mock_route = MagicMock()
        session = navigation.NavigationSession(manager=mock_manager,
                                               voice_generator=mock_voice_generator,
                                               route=mock_route)

        # check the properties
        self.assertEqual(session.manager, mock_manager)
        self.assertEqual(session.voice_generator, mock_voice_generator)
        self.assertEqual(session.route, mock_route)
        self.assertIsNone(session.current_position)
        self.assertIsNone(session.current_turn)
        self.assertIs(session.current_speed, 0)
        self.assertIs(session.average_speed, 0)
        # calling cleanup() with no turns should not crash
        session.cleanup()
        # switching to next turn with no turns should work as well
        session.switch_to_next_turn()
