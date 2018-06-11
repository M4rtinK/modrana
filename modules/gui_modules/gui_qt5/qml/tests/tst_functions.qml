import QtQuick 2.0
import QtTest 1.2
import "../functions.js" as F

TestCase {
    name: "Test functions.js"

    function test_formatBearing() {
        // test bearing formatting
        compare(F.formatBearing(1.11111), 1 + "°")
        compare(F.formatBearing(1.9), 2 + "°")
        compare(F.formatBearing(777.7), 778 + "°")
    }

    function test_formatDistance() {
        // test distance formatting
        compare(F.formatDistance(50, 1), "50.0 m")
        compare(F.formatDistance(50.5, 1), "50.5 m")
        compare(F.formatDistance(50.52513654, 1), "50.5 m")
        compare(F.formatDistance(120, 1), "120 m")
        compare(F.formatDistance(120.4, 1), "120 m")
        compare(F.formatDistance(120.5564867, 1), "121 m")
        compare(F.formatDistance(5000, 1), "5 km")
        compare(F.formatDistance(5400, 1), "5 km")
        compare(F.formatDistance(5600, 1), "6 km")
        compare(F.formatDistance(5600.5, 1), "6 km")
        compare(F.formatDistance(5600.55464, 1), "6 km")
        // check scaling
        compare(F.formatDistance(50, 2), "25.0 m")
        compare(F.formatDistance(50, 4), "12.5 m")
        // check zero distance
        compare(F.formatDistance(0, 1), "0")
        // check scale == 0, this apparently
        // results in infinite distance :)
        compare(F.formatDistance(1, 0), "Infinity km")
    }

    function test_ms2kmh() {
        // test ms -> kmh conversion
        compare(F.ms2kmh(300), 1080.0)
        compare(F.ms2kmh(-300), -1080.0)
        compare(F.ms2kmh(0), 0.0)
    }

}
