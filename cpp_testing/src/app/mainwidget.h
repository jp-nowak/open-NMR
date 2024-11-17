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
    QPushButton* fileButton;
    QPushButton* zoomButton;
    QPushButton* zoomResetButton;

    QPushButton* manualIntegButton;
    QPushButton* removeButton;
    QPushButton* resetIntegralsButton;

    QPushButton* manualPeakButton;
    QPushButton* autoPeakButton;
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
   ActionsWidget* actionsFrame;
   QStackedWidget* spectrumStack;
};



#endif // MAINWIDGET_H


