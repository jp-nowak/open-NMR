qt_add_executable(open-nmr
    mainwidget.h
    mainwidget.cpp
    main.cpp
)

target_link_libraries(open-nmr PRIVATE Qt6::Widgets)

set_target_properties(open-nmr PROPERTIES
    WIN32_EXECUTABLE ON
    MACOSX_BUNDLE ON
)