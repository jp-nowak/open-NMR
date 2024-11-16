#include <QtWidgets>
#include "mainwidget.h"

ActionsWidget::ActionsWidget(QFrame *parent) :
    QFrame(parent)
{
   actions_bt_open = new QPushButton(tr("Open spectra"));
   
   QVBoxLayout *actionsLayout = new QVBoxLayout;
   actionsLayout->addWidget(actions_bt_open);
   setLayout(actionsLayout);
}

// Destructor
ActionsWidget::~ActionsWidget()
{
   delete actions_bt_open;
}

// Constructor for main widget
MainWidget::MainWidget(QWidget *parent) :
    QWidget(parent)
{
   frame_ = new ActionsWidget();
   spectrumViewer_ = new QStackedWidget();

   QHBoxLayout *mainLayout = new QHBoxLayout;
   mainLayout->addWidget(spectrumViewer_);
   mainLayout->addWidget(frame_);
   setLayout(mainLayout);
   setWindowTitle(tr("Open NMR"));
}

// Destructor
MainWidget::~MainWidget()
{
   delete frame_;
   delete spectrumViewer_;
}


