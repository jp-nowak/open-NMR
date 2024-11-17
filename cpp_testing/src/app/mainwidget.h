#ifndef MAINWIDGET_H
#define MAINWIDGET_H

#include <QWidget>
#include <QFrame>

class QFrame;
class QStackedWidget;
class QPushButton;

class ActionsWidget : public QFrame
{
    Q_OBJECT

public:
    explicit ActionsWidget(QFrame *parent = 0); //Constructor
    ~ActionsWidget(); // Destructor

private:
    QPushButton* file_button;
    QPushButton* zoom_button;
    QPushButton* zoom_reset_button;

    QPushButton* manual_integ_button;
    QPushButton* remove_button;
    QPushButton* reset_integrals_button;

    QPushButton* manual_peak_button;
    QPushButton* auto_peak_button;
};

// This is the declaration of our MainWidget class
// The definition/implementation is in mainwidget.cpp
class MainWidget : public QWidget
{
    Q_OBJECT

public:
    explicit MainWidget(QWidget *parent = 0); //Constructor
    ~MainWidget(); // Destructor

private:
   ActionsWidget* frame_;
   QStackedWidget* spectrumViewer_;
};



#endif // MAINWIDGET_H


