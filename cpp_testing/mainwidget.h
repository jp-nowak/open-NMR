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
   QPushButton* actions_bt_open;
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


