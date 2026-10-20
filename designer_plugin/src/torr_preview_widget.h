#pragma once

#include <QColor>
#include <QString>
#include <QWidget>

class QPainter;

class TorrPreviewWidget : public QWidget
{
    Q_OBJECT
    Q_PROPERTY(QString label READ label WRITE setLabel)
    Q_PROPERTY(QString deviceType READ deviceType WRITE setDeviceType)
    Q_PROPERTY(bool online READ online WRITE setOnline)
    Q_PROPERTY(bool switchedOn READ switchedOn WRITE setSwitchedOn)
    Q_PROPERTY(int targetSpeed READ targetSpeed WRITE setTargetSpeed)
    Q_PROPERTY(double pressure READ pressure WRITE setPressure)
    Q_PROPERTY(QString flangeAId READ flangeAId WRITE setFlangeAId)
    Q_PROPERTY(QString flangeBId READ flangeBId WRITE setFlangeBId)
    Q_PROPERTY(QString sourceId READ sourceId WRITE setSourceId)
    Q_PROPERTY(QString targetId READ targetId WRITE setTargetId)
    Q_PROPERTY(QString routeMode READ routeMode WRITE setRouteMode)
    Q_PROPERTY(QString bendPoints READ bendPoints WRITE setBendPoints)
    Q_PROPERTY(QString sourceAnchor READ sourceAnchor WRITE setSourceAnchor)
    Q_PROPERTY(QString targetAnchor READ targetAnchor WRITE setTargetAnchor)

public:
    enum Kind {
        Chamber,
        Turbo,
        Dry,
        Angle,
        Gate,
        Pipe
    };

    explicit TorrPreviewWidget(Kind kind, QWidget *parent = nullptr);

    QSize sizeHint() const override;
    QSize minimumSizeHint() const override;

    Kind kind() const { return m_kind; }
    QString label() const { return m_label; }
    QString deviceType() const { return m_deviceType; }
    bool online() const { return m_online; }
    bool switchedOn() const { return m_switchedOn; }
    int targetSpeed() const { return m_targetSpeed; }
    double pressure() const { return m_pressure; }
    QString flangeAId() const { return m_flangeAId; }
    QString flangeBId() const { return m_flangeBId; }
    QString sourceId() const { return m_sourceId; }
    QString targetId() const { return m_targetId; }
    QString routeMode() const { return m_routeMode; }
    QString bendPoints() const { return m_bendPoints; }
    QString sourceAnchor() const { return m_sourceAnchor; }
    QString targetAnchor() const { return m_targetAnchor; }

    void setLabel(const QString &value);
    void setDeviceType(const QString &value);
    void setOnline(bool value);
    void setSwitchedOn(bool value);
    void setTargetSpeed(int value);
    void setPressure(double value);
    void setFlangeAId(const QString &value);
    void setFlangeBId(const QString &value);
    void setSourceId(const QString &value);
    void setTargetId(const QString &value);
    void setRouteMode(const QString &value);
    void setBendPoints(const QString &value);
    void setSourceAnchor(const QString &value);
    void setTargetAnchor(const QString &value);

    void paintGlyph(QPainter &painter, const QRectF &rect) const;

protected:
    void paintEvent(QPaintEvent *event) override;

private:
    QColor accent() const;
    QString typeName() const;
    QString defaultLabel() const;
    void paintDevice(QPainter &painter, const QRectF &rect);
    void paintPipe(QPainter &painter, const QRectF &rect);
    void paintChamber(QPainter &painter, const QRectF &rect);
    void paintPump(QPainter &painter, const QRectF &rect, bool twin);
    void paintValve(QPainter &painter, const QRectF &rect, bool gate);

    Kind m_kind;
    QString m_label;
    QString m_deviceType;
    bool m_online = true;
    bool m_switchedOn = false;
    int m_targetSpeed = 0;
    double m_pressure = 1.0e-5;
    QString m_flangeAId;
    QString m_flangeBId;
    QString m_sourceId;
    QString m_targetId;
    QString m_routeMode = QStringLiteral("auto");
    QString m_bendPoints;
    QString m_sourceAnchor = QStringLiteral("auto");
    QString m_targetAnchor = QStringLiteral("auto");
};
