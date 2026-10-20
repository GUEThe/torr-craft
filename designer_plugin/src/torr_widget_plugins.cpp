#include "torr_widget_plugins.h"

#include <QIcon>
#include <QPainter>
#include <QPixmap>
#include <QRectF>
#include <QSize>

#include <QtDesigner/QDesignerFormEditorInterface>

namespace {

QString domForDevice(const QString &className,
                     const QString &objectName,
                     const QString &deviceType,
                     const QString &label,
                     const QSize &size,
                     int speed,
                     bool gate)
{
    QString xml;
    xml += QStringLiteral("<ui language=\"c++\">\n");
    xml += QStringLiteral(" <widget class=\"%1\" name=\"%2\">\n")
        .arg(className)
        .arg(objectName);
    xml += QStringLiteral("  <property name=\"geometry\"><rect><x>0</x><y>0</y><width>%1</width><height>%2</height></rect></property>\n")
        .arg(size.width()).arg(size.height());
    xml += QStringLiteral("  <property name=\"deviceType\" stdset=\"0\"><string>%1</string></property>\n").arg(deviceType);
    xml += QStringLiteral("  <property name=\"label\" stdset=\"0\"><string>%1</string></property>\n").arg(label);
    xml += QStringLiteral("  <property name=\"online\" stdset=\"0\"><bool>true</bool></property>\n");
    xml += QStringLiteral("  <property name=\"switchedOn\" stdset=\"0\"><bool>false</bool></property>\n");
    xml += QStringLiteral("  <property name=\"targetSpeed\" stdset=\"0\"><number>%1</number></property>\n").arg(speed);
    xml += QStringLiteral("  <property name=\"pressure\" stdset=\"0\"><double>0.00001</double></property>\n");
    if (gate) {
        xml += QStringLiteral("  <property name=\"flangeAId\" stdset=\"0\"><string></string></property>\n");
        xml += QStringLiteral("  <property name=\"flangeBId\" stdset=\"0\"><string></string></property>\n");
    }
    xml += QStringLiteral(" </widget>\n</ui>\n");
    return xml;
}

QString domForPipe()
{
    QString xml;
    xml += QStringLiteral("<ui language=\"c++\">\n");
    xml += QStringLiteral(" <widget class=\"VacuumPipe\" name=\"vacuumPipe\">\n");
    xml += QStringLiteral("  <property name=\"geometry\"><rect><x>0</x><y>0</y><width>260</width><height>72</height></rect></property>\n");
    xml += QStringLiteral("  <property name=\"sourceId\" stdset=\"0\"><string></string></property>\n");
    xml += QStringLiteral("  <property name=\"targetId\" stdset=\"0\"><string></string></property>\n");
    xml += QStringLiteral("  <property name=\"routeMode\" stdset=\"0\"><string>auto</string></property>\n");
    xml += QStringLiteral("  <property name=\"bendPoints\" stdset=\"0\"><string></string></property>\n");
    xml += QStringLiteral("  <property name=\"sourceAnchor\" stdset=\"0\"><string>auto</string></property>\n");
    xml += QStringLiteral("  <property name=\"targetAnchor\" stdset=\"0\"><string>auto</string></property>\n");
    xml += QStringLiteral(" </widget>\n</ui>\n");
    return xml;
}

QString deviceTypeFor(TorrPreviewWidget::Kind kind)
{
    switch (kind) {
    case TorrPreviewWidget::Chamber:
        return QStringLiteral("chamber");
    case TorrPreviewWidget::Turbo:
        return QStringLiteral("turbo");
    case TorrPreviewWidget::Dry:
        return QStringLiteral("dry");
    case TorrPreviewWidget::Angle:
        return QStringLiteral("angle");
    case TorrPreviewWidget::Gate:
        return QStringLiteral("gate");
    case TorrPreviewWidget::Pipe:
        return QStringLiteral("pipe");
    }
    return QString();
}

QString defaultLabelFor(TorrPreviewWidget::Kind kind)
{
    switch (kind) {
    case TorrPreviewWidget::Chamber:
        return QStringLiteral("工艺腔");
    case TorrPreviewWidget::Turbo:
        return QStringLiteral("分子泵 01");
    case TorrPreviewWidget::Dry:
        return QStringLiteral("干泵 01");
    case TorrPreviewWidget::Angle:
        return QStringLiteral("角阀 01");
    case TorrPreviewWidget::Gate:
        return QStringLiteral("插板阀 01");
    case TorrPreviewWidget::Pipe:
        return QStringLiteral("真空管道");
    }
    return QStringLiteral("元件");
}

} // namespace

TorrWidgetPlugin::TorrWidgetPlugin(const QString &className,
                                   TorrPreviewWidget::Kind kind,
                                   const QString &includeFile,
                                   const QString &iconName,
                                   QObject *parent)
    : QObject(parent)
    , m_className(className)
    , m_kind(kind)
    , m_includeFile(includeFile)
    , m_iconName(iconName)
{
    Q_UNUSED(m_iconName)
}

QString TorrWidgetPlugin::name() const
{
    return m_className;
}

QString TorrWidgetPlugin::group() const
{
    return QStringLiteral("Torr Craft 真空元件");
}

QString TorrWidgetPlugin::toolTip() const
{
    return QStringLiteral("Torr Craft 真空系统元件（Designer 预览）");
}

QString TorrWidgetPlugin::whatsThis() const
{
    return toolTip();
}

QString TorrWidgetPlugin::includeFile() const
{
    return m_includeFile;
}

QIcon TorrWidgetPlugin::icon() const
{
    QPixmap pixmap(48, 48);
    pixmap.fill(Qt::transparent);
    QPainter painter(&pixmap);
    painter.setRenderHint(QPainter::Antialiasing, true);
    TorrPreviewWidget preview(m_kind);
    preview.paintGlyph(painter, QRectF(4, 4, 40, 40));
    return QIcon(pixmap);
}

bool TorrWidgetPlugin::isContainer() const
{
    return false;
}

QWidget *TorrWidgetPlugin::createWidget(QWidget *parent)
{
    auto *widget = new TorrPreviewWidget(m_kind, parent);
    widget->setLabel(defaultLabelFor(m_kind));
    widget->setDeviceType(deviceTypeFor(m_kind));
    if (m_kind == TorrPreviewWidget::Turbo)
        widget->setTargetSpeed(42000);
    else if (m_kind == TorrPreviewWidget::Dry)
        widget->setTargetSpeed(1800);
    else if (m_kind == TorrPreviewWidget::Chamber)
        widget->setPressure(3.2e-7);
    return widget;
}

bool TorrWidgetPlugin::isInitialized() const
{
    return m_initialized;
}

void TorrWidgetPlugin::initialize(QDesignerFormEditorInterface *formEditor)
{
    Q_UNUSED(formEditor)
    m_initialized = true;
}

QString TorrWidgetPlugin::domXml() const
{
    if (m_kind == TorrPreviewWidget::Pipe)
        return domForPipe();

    QSize size(234, 128);
    int speed = 0;
    switch (m_kind) {
    case TorrPreviewWidget::Chamber:
        size = QSize(260, 168);
        break;
    case TorrPreviewWidget::Turbo:
        size = QSize(234, 128);
        speed = 42000;
        break;
    case TorrPreviewWidget::Dry:
        size = QSize(216, 118);
        speed = 1800;
        break;
    case TorrPreviewWidget::Angle:
        size = QSize(126, 96);
        break;
    case TorrPreviewWidget::Gate:
        size = QSize(146, 106);
        break;
    default:
        break;
    }
    const QString objectName = m_className.left(1).toLower() + m_className.mid(1);
    return domForDevice(m_className,
                        objectName,
                        deviceTypeFor(m_kind),
                        defaultLabelFor(m_kind),
                        size,
                        speed,
                        m_kind == TorrPreviewWidget::Gate);
}

TorrWidgetCollection::TorrWidgetCollection(QObject *parent)
    : QObject(parent)
{
    m_widgets << new TorrWidgetPlugin(
        QStringLiteral("ChamberWidget"), TorrPreviewWidget::Chamber,
        QStringLiteral("torr_craft.components.devices"),
        QStringLiteral("chamber"), this);
    m_widgets << new TorrWidgetPlugin(
        QStringLiteral("MolecularPumpWidget"), TorrPreviewWidget::Turbo,
        QStringLiteral("torr_craft.components.devices"),
        QStringLiteral("turbo"), this);
    m_widgets << new TorrWidgetPlugin(
        QStringLiteral("DryPumpWidget"), TorrPreviewWidget::Dry,
        QStringLiteral("torr_craft.components.devices"),
        QStringLiteral("dry"), this);
    m_widgets << new TorrWidgetPlugin(
        QStringLiteral("AngleValveWidget"), TorrPreviewWidget::Angle,
        QStringLiteral("torr_craft.components.devices"),
        QStringLiteral("angle"), this);
    m_widgets << new TorrWidgetPlugin(
        QStringLiteral("GateValveWidget"), TorrPreviewWidget::Gate,
        QStringLiteral("torr_craft.components.devices"),
        QStringLiteral("gate"), this);
    m_widgets << new TorrWidgetPlugin(
        QStringLiteral("VacuumPipe"), TorrPreviewWidget::Pipe,
        QStringLiteral("torr_craft.components.pipe"),
        QStringLiteral("pipe"), this);
}

QList<QDesignerCustomWidgetInterface *> TorrWidgetCollection::customWidgets() const
{
    return m_widgets;
}
