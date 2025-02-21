import dearpygui.dearpygui as dpg

dpg.create_context()

with dpg.theme() as error_theme:
    with dpg.theme_component():
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBar, (96, 0, 0, 255), category=dpg.mvThemeCat_Nodes
        )
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBarHovered,
            (96, 0, 0, 150),
            category=dpg.mvThemeCat_Nodes,
        )
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBarSelected,
            (96, 0, 0, 150),
            category=dpg.mvThemeCat_Nodes,
        )

with dpg.theme() as warning_theme:
    with dpg.theme_component():
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBar, (96, 96, 0, 255), category=dpg.mvThemeCat_Nodes
        )
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBarHovered,
            (96, 96, 0, 150),
            category=dpg.mvThemeCat_Nodes,
        )
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBarSelected,
            (96, 96, 0, 150),
            category=dpg.mvThemeCat_Nodes,
        )

with dpg.theme() as success_theme:
    with dpg.theme_component():
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBar, (0, 96, 32, 255), category=dpg.mvThemeCat_Nodes
        )
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBarHovered,
            (0, 96, 32, 150),
            category=dpg.mvThemeCat_Nodes,
        )
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBarSelected,
            (0, 96, 32, 150),
            category=dpg.mvThemeCat_Nodes,
        )

with dpg.theme() as delinked_theme:
    with dpg.theme_component():
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBar, (96, 0, 96, 255), category=dpg.mvThemeCat_Nodes
        )
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBarHovered,
            (96, 0, 96, 150),
            category=dpg.mvThemeCat_Nodes,
        )
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBarSelected,
            (96, 0, 96, 150),
            category=dpg.mvThemeCat_Nodes,
        )

with dpg.theme() as linked_theme:
    with dpg.theme_component():
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBar, (0, 96, 96, 255), category=dpg.mvThemeCat_Nodes
        )
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBarHovered,
            (0, 96, 96, 150),
            category=dpg.mvThemeCat_Nodes,
        )
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBarSelected,
            (0, 96, 96, 150),
            category=dpg.mvThemeCat_Nodes,
        )
        
with dpg.theme() as executing_theme:
    with dpg.theme_component():
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBar, (0, 0, 96, 255), category=dpg.mvThemeCat_Nodes
        )
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBarHovered,
            (0, 0, 96, 150),
            category=dpg.mvThemeCat_Nodes,
        )
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBarSelected,
            (0, 0, 96, 150),
            category=dpg.mvThemeCat_Nodes,
        )