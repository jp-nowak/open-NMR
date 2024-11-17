#include <QtWidgets>
#include "mainwidget.h"

void onOpenFileClicked() {
    // Open a file dialog to select a file
    QString fileName = QFileDialog::getOpenFileName(nullptr, "Open File", "", "Text Files (*.txt);;All Files (*)");

    if (fileName.isEmpty()) {
        return; // If no file is selected, return
    }

    QFile file(fileName);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) {
        QMessageBox::warning(nullptr, "Error", "Could not open the file!");
        return;
    }

    // Read the file content
    QTextStream in(&file);
    QString fileContent = in.readAll();
    file.close();

    // Show the file content in a message box
    QMessageBox::information(nullptr, "File Content", fileContent);
}

ActionsWidget::ActionsWidget(QFrame *parent) :
    QFrame(parent)
{
   // Viewing buttons
   QPushButton *fileButton = new QPushButton(tr("Open File"));
   QPushButton *zoomButton = new QPushButton(tr("Zoom"));
   QPushButton *zoomResetButton = new QPushButton(tr("Reset Zoom"));

   // Integration buttons
   QPushButton *manualIntegButton = new QPushButton(tr("Manual Integration"));
   QPushButton *removeButton = new QPushButton(tr("Remove Integral"));
   QPushButton *resetIntegralsButton = new QPushButton(tr("Reset Integrals"));

   // Other buttons
   QPushButton *manualPeakButton = new QPushButton(tr("Manual Peaks"));
   QPushButton *autoPeakButton = new QPushButton(tr("Auto Signal"));

   // Set checkable properties
   zoomButton->setCheckable(true);
   manualIntegButton->setCheckable(true);
   removeButton->setCheckable(true);
   manualPeakButton->setCheckable(true);
   autoPeakButton->setCheckable(true);

   // Button connections
   QObject::connect(fileButton, &QPushButton::clicked, &onOpenFileClicked);

   // Layout setup
   QVBoxLayout *actionsLayout = new QVBoxLayout;
   actionsLayout->addWidget(new QLabel(tr("Viewing")));
   actionsLayout->addWidget(fileButton);
   actionsLayout->addWidget(zoomButton);
   actionsLayout->addWidget(zoomResetButton);

   actionsLayout->addWidget(new QLabel(tr("Integration")));
   actionsLayout->addWidget(manualIntegButton);
   actionsLayout->addWidget(removeButton);
   actionsLayout->addWidget(resetIntegralsButton);

   actionsLayout->addWidget(new QLabel(tr("Other")));
   actionsLayout->addWidget(manualPeakButton);
   actionsLayout->addWidget(autoPeakButton);
   actionsLayout->setAlignment(Qt::AlignTop);

   // Set layout
   setLayout(actionsLayout);
}

// Destructor
ActionsWidget::~ActionsWidget()
{
   delete fileButton;
   delete zoomButton;
   delete zoomResetButton;

   delete manualIntegButton;
   delete removeButton;
   delete resetIntegralsButton;

   delete manualPeakButton;
   delete autoPeakButton;
}


// Constructor for main widget
MainWidget::MainWidget(QWidget *parent) :
    QWidget(parent)
{
   actionsFrame = new ActionsWidget();
   spectrumStack = new QStackedWidget();

   QHBoxLayout *mainLayout = new QHBoxLayout;
   mainLayout->addWidget(spectrumStack);
   mainLayout->addWidget(actionsFrame);
   setLayout(mainLayout);
   setWindowTitle(tr("Open NMR"));
}

// Destructor
MainWidget::~MainWidget()
{
   delete actionsFrame;
   delete spectrumStack;
}


