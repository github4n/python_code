import PySimpleGUI as sg

layout = [
    [sg.Text("请输入用户名")],
    [sg.Input("222", key="input1"), sg.Input("123")],
    [sg.Ok()],
]

window  = sg.Window('这是一个测试', layout, auto_size_text=True, default_element_size=(40, 1))


while True:
    event, values = window.Read()
    if event is None or event == 'Exit':
        break
    print(event, values)

    window.Element('_OUTPUT_').Update(values['_IN_'])

window.Close()
