#ifdef QT_QML_DEBUG
#include <QtQuick>
#endif

#ifdef SAILFISH
#include <sailfishapp.h>
#include <QScopedPointer>
#endif

#include <QDebug>
#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQuickView>
#include <QQuickItem>

int main(int argc, char *argv[])
{
    // define the main variables
    QByteArray python_path = PYTHON_PATH;
    QString uc_backend_path = QString(UC_ROOT_PATH) + "/" + QString(UC_BACKEND_FOLDER_NAME);
    QString modrana_main_qml = MODRANA_MAIN_QML;

    // print their value for debugging pruposes
    qDebug() << "modRana launcher running";
    qDebug() << "Python path: " << python_path;
    qDebug() << "UC backend path: " << uc_backend_path;
    qDebug() << "modRana main.qml: " << modrana_main_qml;

    // set PYTHON path based on value from the pro file
    qputenv("PYTHONPATH", python_path);

    // Load the QML file, append the import path and start the application and run the application.
    // This is generally platform specific.
#ifdef SAILFISH
    // start by adding "-d jolla" to argv so that modRana always started with the Jolla/Sailfish OS
    // specific device module by default, skipping potentially fragile platform detection
    std::vector<char*> new_argv(argv, argv + argc);
    new_argv.push_back("-d");
    new_argv.push_back("jolla");
    argv = new_argv.data();
    argc = argc + 2;
    // instantiate the application and view
    QScopedPointer<QGuiApplication> app(SailfishApp::application(argc, argv));
    QScopedPointer<QQuickView> view(SailfishApp::createView());
    // add controls folder to QML import path based on value from pro file
    view->engine()->addImportPath(uc_backend_path);
    view->setSource(QUrl(modrana_main_qml));
    // tell QML that a native launcher is in use
    QQuickItem *root = view->rootObject();
    root->setProperty("nativeLauncher", bool(1));
    view->show();
    return app->exec();
#else
    QGuiApplication app(argc, argv);
    QQmlApplicationEngine engine;
    engine.addImportPath(uc_backend_path);
    engine.load(QUrl(modrana_main_qml));
    // make sure the main QML element is visible
    // - I seem to remember we don't set that property in the QML file for some reason (Silica/Android ?)
    //   so let's do it here
    QObject *root = engine.rootObjects()[0];
    root->setProperty("visible", bool(1));
    // tell QML that a native launcher is in use
    root->setProperty("nativeLauncher", bool(1));
    return app.exec();
#endif
}
