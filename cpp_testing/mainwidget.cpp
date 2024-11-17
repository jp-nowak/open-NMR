#include <QtWidgets>
#include "mainwidget.h"

ActionsWidget::ActionsWidget(QFrame *parent) :
    QFrame(parent)
{
   // Viewing buttons
   QPushButton *file_button = new QPushButton(tr("Open File"));
   QPushButton *zoom_button = new QPushButton(tr("Zoom"));
   zoom_button->setCheckable(true);
   QPushButton *zoom_reset_button = new QPushButton(tr("Reset Zoom"));

   // Integration buttons
   QPushButton *manual_integ_button = new QPushButton(tr("Manual Integration"));
   manual_integ_button->setCheckable(true);
   QPushButton *remove_button = new QPushButton(tr("Remove Integral"));
   remove_button->setCheckable(true);
   QPushButton *reset_integrals_button = new QPushButton(tr("Reset Integrals"));

   // Other buttons
   QPushButton *manual_peak_button = new QPushButton(tr("Manual Peaks"));
   manual_peak_button->setCheckable(true);
   QPushButton *auto_peak_button = new QPushButton(tr("Auto Signal"));
   auto_peak_button->setCheckable(true);

   // Layout setup
   QVBoxLayout *actionsLayout = new QVBoxLayout;
   actionsLayout->addWidget(new QLabel(tr("Viewing")));
   actionsLayout->addWidget(file_button);
   actionsLayout->addWidget(zoom_button);
   actionsLayout->addWidget(zoom_reset_button);

   actionsLayout->addWidget(new QLabel(tr("Integration")));
   actionsLayout->addWidget(manual_integ_button);
   actionsLayout->addWidget(remove_button);
   actionsLayout->addWidget(reset_integrals_button);

   actionsLayout->addWidget(new QLabel(tr("Other")));
   actionsLayout->addWidget(manual_peak_button);
   actionsLayout->addWidget(auto_peak_button);
   actionsLayout->setAlignment(Qt::AlignTop);

   // Set layout
   setLayout(actionsLayout);
}

// Destructor
ActionsWidget::~ActionsWidget()
{
   delete file_button;
   delete zoom_button;
   delete zoom_reset_button;

   delete manual_integ_button;
   delete remove_button;
   delete reset_integrals_button;

   delete manual_peak_button;
   delete auto_peak_button;
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


