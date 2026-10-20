#pragma once

#include <QIcon>
#include <QList>
#include <QObject>
#include <QString>
#include <QtPlugin>

#include <QtDesigner/QDesignerCustomWidgetCollectionInterface>
#include <QtDesigner/QDesignerCustomWidgetInterface>

#include "torr_preview_widget.h"

class TorrWidgetPlugin : public QObject, public QDesignerCustomWidgetInterface
{
    Q_OBJECT
    Q_INTERFACES(QDesignerCustomWidgetInterface)

public:
    TorrWidgetPlugin(const QString &className,
                     TorrPreviewWidget::Kind kind,
                     const QString &includeFile,
                     const QString &iconName,
                     QObject *parent = nullptr);

    QString name() const override;
    QString group() const override;
    QString toolTip() const override;
    QString whatsThis() const override;
    QString includeFile() const override;
    QIcon icon() const override;
    bool isContainer() const override;
    QWidget *createWidget(QWidget *parent) override;
    bool isInitialized() const override;
    void initialize(QDesignerFormEditorInterface *formEditor) override;
    QString domXml() const override;

private:
    QString m_className;
    TorrPreviewWidget::Kind m_kind;
    QString m_includeFile;
    QString m_iconName;
    bool m_initialized = false;
};

class TorrWidgetCollection : public QObject, public QDesignerCustomWidgetCollectionInterface
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID "org.qt-project.Qt.QDesignerCustomWidgetCollectionInterface")
    Q_INTERFACES(QDesignerCustomWidgetCollectionInterface)

public:
    explicit TorrWidgetCollection(QObject *parent = nullptr);
    QList<QDesignerCustomWidgetInterface *> customWidgets() const override;

private:
    QList<QDesignerCustomWidgetInterface *> m_widgets;
};
