#include "torr_preview_widget.h"

#include <QFont>
#include <QFontMetrics>
#include <QLinearGradient>
#include <QLocale>
#include <QPainter>
#include <QPainterPath>
#include <QPen>
#include <QPolygonF>

#include <algorithm>
#include <cmath>

namespace {

QColor color(const char *value, int alpha = 255)
{
    QColor c(QString::fromLatin1(value));
    c.setAlpha(alpha);
    return c;
}

QColor accentFor(TorrPreviewWidget::Kind kind)
{
    switch (kind) {
    case TorrPreviewWidget::Chamber:
        return QColor("#7dd3fc");
    case TorrPreviewWidget::Turbo:
        return QColor("#34d399");
    case TorrPreviewWidget::Dry:
        return QColor("#fbbf24");
    case TorrPreviewWidget::Angle:
        return QColor("#fb923c");
    case TorrPreviewWidget::Gate:
        return QColor("#a78bfa");
    case TorrPreviewWidget::Pipe:
        return QColor("#22d3ee");
    }
    return QColor("#22d3ee");
}

QFont uiFont(int pixels, int weight = QFont::Normal)
{
    QFont font(QStringLiteral("Microsoft YaHei UI"));
    font.setPixelSize(std::max(7, pixels));
    font.setWeight(weight);
    return font;
}

QFont monoFont(int pixels, int weight = QFont::Bold)
{
    QFont font(QStringLiteral("Consolas"));
    font.setPixelSize(std::max(7, pixels));
    font.setWeight(weight);
    return font;
}

} // namespace

TorrPreviewWidget::TorrPreviewWidget(Kind kind, QWidget *parent)
    : QWidget(parent)
    , m_kind(kind)
    , m_label(defaultLabel())
    , m_deviceType(QString::number(static_cast<int>(kind)))
{
    switch (kind) {
    case Chamber:
        resize(260, 168);
        m_pressure = 3.2e-7;
        setMinimumSize(176, 124);
        break;
    case Turbo:
        resize(234, 128);
        m_targetSpeed = 42000;
        setMinimumSize(174, 106);
        break;
    case Dry:
        resize(216, 118);
        m_targetSpeed = 1800;
        setMinimumSize(166, 98);
        break;
    case Angle:
        resize(126, 96);
        setMinimumSize(96, 76);
        break;
    case Gate:
        resize(146, 106);
        setMinimumSize(112, 84);
        break;
    case Pipe:
        resize(260, 72);
        setMinimumSize(100, 44);
        break;
    }
    setAttribute(Qt::WA_NoSystemBackground, true);
    setAutoFillBackground(false);
}

QSize TorrPreviewWidget::sizeHint() const
{
    switch (m_kind) {
    case Chamber:
        return QSize(260, 168);
    case Turbo:
        return QSize(234, 128);
    case Dry:
        return QSize(216, 118);
    case Angle:
        return QSize(126, 96);
    case Gate:
        return QSize(146, 106);
    case Pipe:
        return QSize(260, 72);
    }
    return QSize(200, 120);
}

QSize TorrPreviewWidget::minimumSizeHint() const
{
    return minimumSize();
}

QColor TorrPreviewWidget::accent() const
{
    return accentFor(m_kind);
}

QString TorrPreviewWidget::typeName() const
{
    switch (m_kind) {
    case Chamber:
        return QStringLiteral("VACUUM CHAMBER");
    case Turbo:
        return QStringLiteral("TURBO PUMP");
    case Dry:
        return QStringLiteral("DRY PUMP");
    case Angle:
        return QStringLiteral("ANGLE VALVE");
    case Gate:
        return QStringLiteral("GATE VALVE");
    case Pipe:
        return QStringLiteral("VACUUM PIPE");
    }
    return QString();
}

QString TorrPreviewWidget::defaultLabel() const
{
    switch (m_kind) {
    case Chamber:
        return QStringLiteral("工艺腔");
    case Turbo:
        return QStringLiteral("分子泵 01");
    case Dry:
        return QStringLiteral("干泵 01");
    case Angle:
        return QStringLiteral("角阀 01");
    case Gate:
        return QStringLiteral("插板阀 01");
    case Pipe:
        return QStringLiteral("真空管道");
    }
    return QStringLiteral("元件");
}

void TorrPreviewWidget::setLabel(const QString &value)
{
    if (m_label == value)
        return;
    m_label = value;
    update();
}

void TorrPreviewWidget::setDeviceType(const QString &value)
{
    m_deviceType = value;
}

void TorrPreviewWidget::setOnline(bool value)
{
    if (m_online == value)
        return;
    m_online = value;
    update();
}

void TorrPreviewWidget::setSwitchedOn(bool value)
{
    if (m_switchedOn == value)
        return;
    m_switchedOn = value;
    update();
}

void TorrPreviewWidget::setTargetSpeed(int value)
{
    value = std::max(0, value);
    if (m_targetSpeed == value)
        return;
    m_targetSpeed = value;
    update();
}

void TorrPreviewWidget::setPressure(double value)
{
    m_pressure = value;
    update();
}

void TorrPreviewWidget::setFlangeAId(const QString &value)
{
    m_flangeAId = value;
    update();
}

void TorrPreviewWidget::setFlangeBId(const QString &value)
{
    m_flangeBId = value;
    update();
}

void TorrPreviewWidget::setSourceId(const QString &value)
{
    m_sourceId = value;
    update();
}

void TorrPreviewWidget::setTargetId(const QString &value)
{
    m_targetId = value;
    update();
}

void TorrPreviewWidget::setRouteMode(const QString &value)
{
    m_routeMode = value;
    update();
}

void TorrPreviewWidget::setBendPoints(const QString &value)
{
    m_bendPoints = value;
    update();
}

void TorrPreviewWidget::setSourceAnchor(const QString &value)
{
    m_sourceAnchor = value;
    update();
}

void TorrPreviewWidget::setTargetAnchor(const QString &value)
{
    m_targetAnchor = value;
    update();
}

void TorrPreviewWidget::paintEvent(QPaintEvent *event)
{
    Q_UNUSED(event)
    QPainter painter(this);
    painter.setRenderHint(QPainter::Antialiasing, true);
    const QRectF r = QRectF(rect()).adjusted(1, 1, -1, -1);
    if (m_kind == Pipe) {
        paintPipe(painter, r);
        return;
    }
    paintDevice(painter, r);
}

void TorrPreviewWidget::paintDevice(QPainter &p, const QRectF &r)
{
    const QColor accentColor = accent();

    p.setPen(Qt::NoPen);
    p.setBrush(color("#000000", 75));
    p.drawRoundedRect(r.translated(0, 2.4), 13, 13);

    QLinearGradient gradient(r.topLeft(), r.bottomLeft());
    gradient.setColorAt(0.0, QColor("#18263b"));
    gradient.setColorAt(0.55, QColor("#111e31"));
    gradient.setColorAt(1.0, QColor("#0c1727"));
    p.setBrush(gradient);
    p.setPen(QPen(QColor("#31445d"), 1.0));
    p.drawRoundedRect(r, 12, 12);

    QLinearGradient sheen(r.topLeft(), r.topRight());
    sheen.setColorAt(0.0, QColor(accentColor.red(), accentColor.green(), accentColor.blue(), 28));
    sheen.setColorAt(0.35, QColor(accentColor.red(), accentColor.green(), accentColor.blue(), 0));
    p.setBrush(sheen);
    p.setPen(Qt::NoPen);
    p.drawRoundedRect(r.adjusted(1, 1, -1, -1), 11, 11);

    p.setBrush(accentColor);
    p.drawRoundedRect(QRectF(r.left() + 12, r.top() + 11, 3, std::min(20.0, r.height() - 22)), 1.5, 1.5);

    const double x = r.left() + 22;
    const double top = r.top() + 10;

    QFont typeFont = uiFont(7, QFont::DemiBold);
    typeFont.setLetterSpacing(QFont::AbsoluteSpacing, 1.1);
    p.setFont(typeFont);
    p.setPen(accentColor);

    double reserved = 0;
    if (m_kind != Chamber) {
        const QString onlineText = m_online ? QStringLiteral("在线") : QStringLiteral("离线");
        const QColor onlineColor = m_online ? QColor("#34d399") : QColor("#64748b");
        QFont statusFont = uiFont(8, QFont::DemiBold);
        p.setFont(statusFont);
        reserved = QFontMetrics(statusFont).horizontalAdvance(onlineText) + 18;
        p.setPen(onlineColor);
        p.drawText(QRectF(r.right() - reserved, top - 1, reserved, 13),
                   Qt::AlignRight | Qt::AlignVCenter, onlineText);
        p.setBrush(onlineColor);
        p.setPen(Qt::NoPen);
        p.drawEllipse(QPointF(r.right() - reserved - 1, top + 5.2), 2.6, 2.6);
    }

    const double available = std::max(20.0, r.width() - 44 - reserved);
    p.setFont(typeFont);
    p.setPen(accentColor);
    QString type = typeName();
    if (r.width() < 150)
        type = type.section(' ', 0, 0);
    p.drawText(QRectF(x, top, available, 12), Qt::AlignLeft | Qt::AlignVCenter, type);

    QFont labelFont = uiFont(12, QFont::DemiBold);
    p.setFont(labelFont);
    p.setPen(QColor("#e6eef8"));
    const QString label = QFontMetrics(labelFont).elidedText(
        m_label, Qt::ElideRight, static_cast<int>(std::max(30.0, r.width() - 40)));
    p.drawText(QRectF(x, top + 14, r.width() - 36, 20), Qt::AlignLeft | Qt::AlignVCenter, label);

    if (m_kind == Chamber) {
        paintChamber(p, r);
    } else if (m_kind == Turbo || m_kind == Dry) {
        paintPump(p, r, m_kind == Dry);
    } else {
        paintValve(p, r, m_kind == Gate);
    }
}

void TorrPreviewWidget::paintChamber(QPainter &p, const QRectF &r)
{
    const QColor accentColor = accent();
    const QRectF inner = r.adjusted(11, 48, -11, -42);
    if (inner.width() > 8 && inner.height() > 8) {
        QLinearGradient gradient(inner.topLeft(), inner.bottomRight());
        gradient.setColorAt(0.0, QColor("#0a1626"));
        gradient.setColorAt(0.62, QColor("#0d1d30"));
        gradient.setColorAt(1.0, QColor("#10263a"));
        p.setBrush(gradient);
        p.setPen(QPen(QColor(accentColor.red(), accentColor.green(), accentColor.blue(), 58), 1.0));
        p.drawRoundedRect(inner, 8, 8);
    }

    p.setPen(accentColor);
    p.setFont(uiFont(7, QFont::DemiBold));
    p.drawText(QRectF(r.right() - 70, r.top() + 8, 56, 14),
               Qt::AlignRight | Qt::AlignVCenter, QStringLiteral("VESSEL"));

    const QString pressureText = m_pressure > 0
        ? QString::number(m_pressure, 'e', 1)
        : QStringLiteral("—");
    p.setFont(monoFont(r.width() > 230 ? 22 : 18));
    p.setPen(QColor("#e6eef8"));
    p.drawText(QRectF(r.left() + 24, r.top() + 58, r.width() * 0.56, 32),
               Qt::AlignLeft | Qt::AlignVCenter, pressureText);

    p.setFont(uiFont(8, QFont::DemiBold));
    p.setPen(QColor("#94a3b8"));
    p.drawText(QRectF(r.left() + 25, r.top() + 90, 120, 13),
               Qt::AlignLeft | Qt::AlignVCenter, QStringLiteral("PRESSURE · mbar"));

    if (r.height() >= 140) {
        p.setPen(accentColor);
        p.drawText(QRectF(r.left() + 24, r.bottom() - 31, 90, 14),
                   Qt::AlignLeft | Qt::AlignVCenter,
                   m_pressure < 1.0 ? QStringLiteral("READY") : QStringLiteral("ROUGH"));
    }
}

void TorrPreviewWidget::paintPump(QPainter &p, const QRectF &r, bool twin)
{
    const QColor accentColor = accent();
    const bool hasRotor = r.width() >= 198 && r.height() >= 110;
    double rotorDiameter = std::min(52.0, r.height() * 0.44);
    QRectF rotorRect(r.right() - rotorDiameter - 17,
                     r.top() + (r.height() - rotorDiameter) / 2.0 + 4,
                     rotorDiameter, rotorDiameter);

    auto drawRotor = [&](const QRectF &rect, int blades) {
        p.setPen(Qt::NoPen);
        p.setBrush(QColor(accentColor.red(), accentColor.green(), accentColor.blue(), 38));
        p.drawEllipse(rect);
        p.setBrush(QColor("#0a1524"));
        p.setPen(QPen(QColor(accentColor.red(), accentColor.green(), accentColor.blue(), 95), 1.2));
        p.drawEllipse(rect.adjusted(3, 3, -3, -3));
        const QPointF center = rect.center();
        const double radius = rect.width() * 0.31;
        p.setPen(QPen(QColor(accentColor.red(), accentColor.green(), accentColor.blue(), 190), 1.4));
        for (int i = 0; i < blades; ++i) {
            const double angle = (360.0 / blades) * i * 3.141592653589793 / 180.0;
            p.drawLine(center, QPointF(center.x() + std::cos(angle) * radius,
                                       center.y() + std::sin(angle) * radius));
        }
        p.setBrush(accentColor);
        p.setPen(Qt::NoPen);
        p.drawEllipse(center, 3.2, 3.2);
    };

    if (hasRotor) {
        if (twin) {
            const double d = std::min(32.0, rotorRect.width() * 0.62);
            drawRotor(QRectF(rotorRect.left(), rotorRect.center().y() - d / 2, d, d), 4);
            drawRotor(QRectF(rotorRect.right() - d, rotorRect.center().y() - d / 2, d, d), 4);
        } else {
            drawRotor(rotorRect, 7);
        }
    }

    const QString chipText = m_switchedOn ? QStringLiteral("运行中") : QStringLiteral("已停止");
    QFont chipFont = uiFont(8, QFont::DemiBold);
    p.setFont(chipFont);
    const double chipWidth = std::max(46.0,
        static_cast<double>(QFontMetrics(chipFont).horizontalAdvance(chipText)) + 18);
    QRectF chip(r.left() + 22, r.top() + 51, chipWidth, 19);
    const QColor chipColor = (m_switchedOn && m_online) ? QColor("#34d399") : QColor("#94a3b8");
    p.setBrush(QColor(chipColor.red(), chipColor.green(), chipColor.blue(), 28));
    p.setPen(QPen(QColor(chipColor.red(), chipColor.green(), chipColor.blue(), 80), 1.0));
    p.drawRoundedRect(chip, 9.5, 9.5);
    p.setPen(chipColor);
    p.drawText(chip, Qt::AlignCenter, chipText);

    const QString speedText = m_online
        ? QLocale(QLocale::English).toString(m_targetSpeed)
        : QStringLiteral("--");
    p.setFont(monoFont(r.width() > 190 ? 20 : 17));
    p.setPen(m_online ? QColor("#e6eef8") : QColor("#64748b"));
    const double speedWidth = std::max(40.0, (hasRotor ? rotorRect.left() - 8 : r.right() - 14) - r.left() - 20);
    p.drawText(QRectF(r.left() + 20, r.bottom() - 34, speedWidth, 25),
               Qt::AlignLeft | Qt::AlignVCenter, speedText);
    p.setFont(uiFont(7, QFont::DemiBold));
    p.setPen(accentColor);
    const double textWidth = QFontMetrics(monoFont(r.width() > 190 ? 20 : 17))
        .horizontalAdvance(speedText);
    p.drawText(QRectF(r.left() + 25 + textWidth, r.bottom() - 28, 36, 12),
               Qt::AlignLeft | Qt::AlignVCenter, QStringLiteral("RPM"));
}

void TorrPreviewWidget::paintValve(QPainter &p, const QRectF &r, bool gate)
{
    const QColor accentColor = accent();
    const QRectF symbol(r.left() + 17, r.top() + 38,
                        r.width() - 34, std::max(16.0, r.height() - 64));
    const QPointF center = symbol.center();
    p.setPen(QPen(QColor(accentColor.red(), accentColor.green(), accentColor.blue(), 110), 4.0));
    p.drawLine(QPointF(symbol.left() - 12, center.y()), QPointF(symbol.left() + 3, center.y()));
    p.drawLine(QPointF(symbol.right() - 3, center.y()), QPointF(symbol.right() + 12, center.y()));

    p.setBrush(QColor("#0a1524"));
    p.setPen(QPen(accentColor, 1.5));
    if (gate) {
        p.drawRoundedRect(QRectF(center.x() - 22, center.y() - 14, 44, 28), 3, 3);
        p.setBrush(accentColor);
        p.drawRoundedRect(QRectF(center.x() - 4, center.y() - 14, 8, 28), 2, 2);
    } else {
        p.drawPolygon(QPolygonF({
            QPointF(center.x() - 18, center.y() - 14),
            QPointF(center.x(), center.y()),
            QPointF(center.x() - 18, center.y() + 14),
            QPointF(center.x() - 18, center.y() - 14)}));
        p.drawPolygon(QPolygonF({
            QPointF(center.x() + 18, center.y() - 14),
            QPointF(center.x(), center.y()),
            QPointF(center.x() + 18, center.y() + 14),
            QPointF(center.x() + 18, center.y() - 14)}));
    }

    QString chipText;
    if (gate && !m_flangeAId.isEmpty() && !m_flangeBId.isEmpty())
        chipText = m_switchedOn ? QStringLiteral("内联 · 已开启") : QStringLiteral("内联 · 已关闭");
    else
        chipText = m_switchedOn ? QStringLiteral("已开启") : QStringLiteral("已关闭");
    QFont chipFont = uiFont(8, QFont::DemiBold);
    p.setFont(chipFont);
    const double chipWidth = std::max(48.0,
        static_cast<double>(QFontMetrics(chipFont).horizontalAdvance(chipText)) + 20);
    QRectF chip(r.center().x() - chipWidth / 2.0, r.bottom() - 22, chipWidth, 16);
    const QColor chipColor = (m_switchedOn && m_online) ? QColor("#34d399") : QColor("#94a3b8");
    p.setBrush(QColor(chipColor.red(), chipColor.green(), chipColor.blue(), 28));
    p.setPen(QPen(QColor(chipColor.red(), chipColor.green(), chipColor.blue(), 80), 1.0));
    p.drawRoundedRect(chip, 8, 8);
    p.setPen(chipColor);
    p.drawText(chip, Qt::AlignCenter, chipText);
}

void TorrPreviewWidget::paintPipe(QPainter &p, const QRectF &r)
{
    p.setPen(Qt::NoPen);
    p.setBrush(QColor(0, 0, 0, 65));
    p.drawRoundedRect(r.translated(0, 2), 10, 10);
    QLinearGradient gradient(r.topLeft(), r.bottomLeft());
    gradient.setColorAt(0, QColor("#111e31"));
    gradient.setColorAt(1, QColor("#0c1727"));
    p.setBrush(gradient);
    p.setPen(QPen(QColor("#2a3d56"), 1.0));
    p.drawRoundedRect(r, 10, 10);

    const double y = r.center().y();
    QPainterPath path;
    path.moveTo(r.left() + 14, y - 10);
    path.lineTo(r.left() + 46, y - 10);
    path.lineTo(r.left() + 46, y + 8);
    path.lineTo(r.right() - 14, y + 8);
    p.setBrush(Qt::NoBrush);
    p.setPen(QPen(QColor("#263950"), 7.0, Qt::SolidLine, Qt::RoundCap, Qt::RoundJoin));
    p.drawPath(path);
    p.setPen(QPen(QColor("#22d3ee"), 2.2, Qt::SolidLine, Qt::RoundCap, Qt::RoundJoin));
    p.drawPath(path);
    p.setBrush(QColor("#22d3ee"));
    p.setPen(Qt::NoPen);
    p.drawEllipse(QPointF(r.left() + 14, y - 10), 3.5, 3.5);
    p.drawEllipse(QPointF(r.right() - 14, y + 8), 3.5, 3.5);

    p.setFont(uiFont(9, QFont::DemiBold));
    p.setPen(QColor("#c7d5e6"));
    p.drawText(QRectF(r.left() + 14, r.bottom() - 22, r.width() - 28, 16),
               Qt::AlignLeft | Qt::AlignVCenter, m_label);
}

void TorrPreviewWidget::paintGlyph(QPainter &p, const QRectF &rect) const
{
    const QColor accentColor = accent();
    p.save();
    p.translate(rect.topLeft());
    const double scale = std::min(rect.width(), rect.height()) / 48.0;
    p.scale(scale, scale);
    QPen pen(accentColor, 2.0);
    pen.setCapStyle(Qt::RoundCap);
    pen.setJoinStyle(Qt::RoundJoin);
    p.setPen(pen);
    p.setBrush(Qt::NoBrush);

    if (m_kind == Chamber) {
        p.drawRoundedRect(QRectF(7, 10, 34, 28), 5, 5);
        p.drawRoundedRect(QRectF(12, 15, 18, 18), 3, 3);
        p.drawLine(QPointF(3, 24), QPointF(7, 24));
        p.drawLine(QPointF(41, 24), QPointF(45, 24));
    } else if (m_kind == Turbo || m_kind == Dry) {
        p.drawRoundedRect(QRectF(6, 20, 36, 17), 5, 5);
        p.drawEllipse(QPointF(17, 28), 7, 7);
        if (m_kind == Dry)
            p.drawEllipse(QPointF(30, 28), 7, 7);
        p.drawLine(QPointF(31, 20), QPointF(31, 14));
    } else if (m_kind == Gate) {
        p.drawLine(QPointF(4, 30), QPointF(14, 30));
        p.drawLine(QPointF(34, 30), QPointF(44, 30));
        p.drawRect(QRectF(14, 20, 5, 20));
        p.drawRect(QRectF(29, 20, 5, 20));
        p.drawLine(QPointF(19, 20), QPointF(29, 20));
        p.drawLine(QPointF(19, 40), QPointF(29, 40));
    } else if (m_kind == Angle) {
        p.drawLine(QPointF(5, 30), QPointF(45, 30));
        p.drawPolygon(QPolygonF({QPointF(14, 23), QPointF(24, 30), QPointF(14, 37)}));
        p.drawPolygon(QPolygonF({QPointF(34, 23), QPointF(24, 30), QPointF(34, 37)}));
        p.drawLine(QPointF(24, 30), QPointF(24, 16));
    } else {
        QPainterPath path;
        path.moveTo(5, 15);
        path.lineTo(22, 15);
        path.lineTo(22, 33);
        path.lineTo(43, 33);
        p.drawPath(path);
        p.setBrush(accentColor);
        p.drawEllipse(QPointF(5, 15), 3, 3);
        p.drawEllipse(QPointF(43, 33), 3, 3);
    }
    p.restore();
}
