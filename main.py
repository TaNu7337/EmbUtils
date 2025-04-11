import flet as ft

def main(page: ft.Page):
    
    # ウィンドウ名
    page.title = "Flet"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    page


if __name__ == "__main__":
    ft.app(main)
