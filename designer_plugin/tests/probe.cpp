#include <QApplication>
#include <QDesignerCustomWidgetCollectionInterface>
#include <QDesignerCustomWidgetInterface>
#include <QDir>
#include <QFileInfo>
#include <QImage>
#include <QPainter>
#include <QPixmap>
#include <QPluginLoader>
#include <QTextStream>
#include <QWidget>

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    QTextStream out(stdout);

    const QStringList args = app.arguments();
    if (args.size() < 3) {
        out << "usage: probe <plugin.dll> <output-dir>\n";
        return 2;
    }
    const QString pluginPath = QFileInfo(args.at(1)).absoluteFilePath();
    QDir outputDir(args.at(2));
    if (!outputDir.exists() && !QDir().mkpath(outputDir.absolutePath())) {
        out << "cannot create output directory\n";
        return 3;
    }

    QPluginLoader loader(pluginPath);
    QObject *instance = loader.instance();
    if (!instance) {
        out << "LOAD_FAILED " << loader.errorString() << "\n";
        return 4;
    }

    auto *collection = qobject_cast<QDesignerCustomWidgetCollectionInterface *>(instance);
    if (!collection) {
        out << "NOT_A_DESIGNER_COLLECTION\n";
        return 5;
    }

    const auto widgets = collection->customWidgets();
    out << "COLLECTION_LOADED count=" << widgets.size() << "\n";
    for (QDesignerCustomWidgetInterface *factory : widgets) {
        if (!factory)
            continue;
        QWidget *widget = factory->createWidget(nullptr);
        if (!widget) {
            out << "CREATE_FAILED " << factory->name() << "\n";
            return 6;
        }
        widget->resize(widget->sizeHint());
        QPixmap pixmap(widget->size());
        pixmap.fill(QColor("#08111d"));
        QPainter painter(&pixmap);
        widget->render(&painter);
        painter.end();
        const QString path = outputDir.filePath(factory->name() + QStringLiteral(".png"));
        if (!pixmap.save(path, "PNG")) {
            out << "SAVE_FAILED " << path << "\n";
            return 7;
        }
        out << "WIDGET " << factory->name()
            << " include=" << factory->includeFile()
            << " size=" << widget->width() << "x" << widget->height()
            << " properties=" << widget->metaObject()->propertyCount()
            << " preview=" << path << "\n";
        delete widget;
    }
    out << "PROBE_OK\n";
    return 0;
}
