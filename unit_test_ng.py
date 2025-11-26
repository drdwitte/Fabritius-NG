from nicegui import ui


def main():
    ui.label('Fabritius-NG is alive and running!')
    ui.button('Klik hier', on_click=lambda: ui.notify('Test OK'))
    ui.run()



#Waarom extra conditie? 
#NiceGUI gebruikt multiprocessing op Windows (voor websockets, reload, enz.).
#Windows start sub-processen met "__mp_main__" als module-naam.
if __name__ in {"__main__", "__mp_main__"}:

    main()