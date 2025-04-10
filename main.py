import flet as ft
from flet import (
    AppBar,
    ElevatedButton,
    Page,
    Text,
    TextField,
    Column,
    Row,
    Tab,
    Tabs,
    Container,
    Icon,
    icons,
    Dropdown,
    dropdown,
    Divider,
    PopupMenuButton,
    PopupMenuItem,
    FilePicker,
    FilePickerResultEvent,
    DragTarget,
    ResponsiveRow,
    ProgressBar,
    ListView,
    ListTile,
    TextButton,
    Checkbox,
    ScrollMode,
    IconButton,
    Ref,
    TextStyle,
    colors,
)
import os
import re
import binascii


def main(page: ft.Page):
    # アプリ設定
    page.title = "EmbUtils - 便利ツールコレクション"
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.padding = 20
    page.window_width = 900
    page.window_height = 700
    page.window_resizable = True
    
    # ヘッダー部分
    page.appbar = AppBar(
        title=Text("EmbUtils", size=24, weight="bold"),
        center_title=False,
        bgcolor=ft.colors.BLUE_GREY_900,
        actions=[
            PopupMenuButton(
                items=[
                    PopupMenuItem(text="設定"),
                    PopupMenuItem(text="ヘルプ"),
                    PopupMenuItem(text="バージョン情報"),
                ]
            ),
        ],
    )

    # Hexファイル検索ツールのロジック
    hex_content = ft.Ref[ft.TextField]()
    search_query = ft.Ref[ft.TextField]()
    result_view = ft.Ref[ft.ListView]()
    search_status = ft.Ref[ft.Text]()
    context_lines = ft.Ref[ft.TextField]()
    file_path_text = ft.Ref[ft.Text]()
    current_hex_file_path = ""
    hex_ignore_case = ft.Ref[ft.Checkbox]()
    is_binary_search = ft.Ref[ft.Checkbox]()
    search_progress = ft.Ref[ft.ProgressBar]()
    
    # ファイルピッカー
    file_picker = FilePicker(
        on_result=lambda e: process_file_pick(e),
    )
    page.overlay.append(file_picker)

    def process_file_pick(e: FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            nonlocal current_hex_file_path
            file_path = e.files[0].path
            current_hex_file_path = file_path
            file_path_text.current.value = f"ファイル: {os.path.basename(file_path)}"
            file_path_text.current.visible = True
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                hex_content.current.value = content
                page.update()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"ファイル読み込みエラー: {str(ex)}"), 
                    bgcolor=ft.colors.RED_400
                )
                page.snack_bar.open = True
                page.update()

    def process_drop_files(e):
        if len(e.data.files) > 0:
            nonlocal current_hex_file_path
            file_path = e.data.files[0].path
            current_hex_file_path = file_path
            file_path_text.current.value = f"ファイル: {os.path.basename(file_path)}"
            file_path_text.current.visible = True
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                hex_content.current.value = content
                page.update()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"ファイル読み込みエラー: {str(ex)}"), 
                    bgcolor=ft.colors.RED_400
                )
                page.snack_bar.open = True
                page.update()

    def search_hex_file(e):
        """Hexファイル内の検索を実行する"""
        query = search_query.current.value.strip()
        content = hex_content.current.value
        ignore_case = hex_ignore_case.current.value
        binary_search = is_binary_search.current.value
        
        if not query:
            page.snack_bar = ft.SnackBar(content=ft.Text("検索語句を入力してください"))
            page.snack_bar.open = True
            page.update()
            return
            
        if not content:
            page.snack_bar = ft.SnackBar(content=ft.Text("Hexファイルを読み込んでください"))
            page.snack_bar.open = True
            page.update()
            return
            
        try:
            # 進捗表示を開始
            search_progress.current.visible = True
            page.update()
            
            result_view.current.controls.clear()
            
            # 検索の前処理
            lines = content.splitlines()
            context_line_count = int(context_lines.current.value) if context_lines.current.value.isdigit() else 5
            
            search_matches = []
            
            # 検索処理
            if binary_search:
                # バイナリ検索モード - ASCII文字列またはHex値で検索
                if query.startswith("0x"):
                    # Hex値として検索
                    hex_query = query[2:].lower()
                    pattern = re.compile(hex_query, re.IGNORECASE if ignore_case else 0)
                    
                    # Hexパターンを検索
                    for i, line in enumerate(lines):
                        line_hex = ''.join(line.split()).lower()
                        if pattern.search(line_hex):
                            search_matches.append((i, line))
                else:
                    # ASCII文字列をHexに変換して検索
                    ascii_bytes = query.encode('ascii', errors='ignore')
                    hex_pattern = binascii.hexlify(ascii_bytes).decode('ascii')
                    pattern = re.compile(hex_pattern, re.IGNORECASE if ignore_case else 0)
                    
                    for i, line in enumerate(lines):
                        line_hex = ''.join(line.split()).lower()
                        if pattern.search(line_hex):
                            search_matches.append((i, line))
            else:
                # テキスト検索モード
                pattern = re.compile(re.escape(query), re.IGNORECASE if ignore_case else 0)
                for i, line in enumerate(lines):
                    if pattern.search(line):
                        search_matches.append((i, line))
            
            # 検索結果の構築
            for line_idx, line in search_matches:
                # 前後のコンテキスト行を取得
                start_idx = max(0, line_idx - context_line_count)
                end_idx = min(len(lines), line_idx + context_line_count + 1)
                
                context_block = []
                for i in range(start_idx, end_idx):
                    line_text = lines[i]
                    is_match_line = i == line_idx
                    
                    context_block.append(
                        ft.Container(
                            content=ft.Text(
                                f"{i+1}: {line_text}",
                                style=ft.TextStyle(
                                    weight="bold" if is_match_line else "normal",
                                    color=ft.colors.RED if is_match_line else None,
                                ),
                                selectable=True,
                            ),
                            padding=5,
                            bgcolor=ft.colors.AMBER_50 if is_match_line else None,
                        )
                    )
                    
                result_view.current.controls.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Divider(),
                                ft.Text(f"マッチ行: {line_idx+1}", weight="bold"),
                                *context_block,
                            ]
                        ),
                        padding=10,
                        bgcolor=ft.colors.BLUE_GREY_50,
                        border_radius=5,
                        margin=ft.margin.only(bottom=10),
                    )
                )
            
            # 検索結果の表示
            if not result_view.current.controls:
                search_status.current.value = "検索結果: 見つかりませんでした"
            else:
                search_status.current.value = f"検索結果: {len(search_matches)}件見つかりました"
                
            search_status.current.visible = True
            
        except Exception as ex:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"検索エラー: {str(ex)}"),
                bgcolor=ft.colors.RED_400
            )
            page.snack_bar.open = True
        finally:
            # 進捗表示を終了
            search_progress.current.visible = False
            page.update()

    def clear_hex_content(e):
        """入力と検索結果をクリアする"""
        hex_content.current.value = ""
        result_view.current.controls.clear()
        search_status.current.visible = False
        file_path_text.current.visible = False
        page.update()
        
    # Hexタブに移動する関数
    def navigate_to_hex_tab(e):
        tabs.selected_index = 3
        page.update()

    # タブ構造の定義
    def on_tab_change(e):
        print(f"選択されたタブ: {e.control.selected_index}")

    tabs = Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            Tab(
                text="ホーム",
                icon=ft.icons.HOME,
                content=Container(
                    content=Column(
                        controls=[
                            Text("EmbUtilsへようこそ！", size=24),
                            Text("利用したいツールを選択してください", size=16),
                            Divider(),
                            Row(
                                controls=[
                                    ElevatedButton(
                                        text="ツール1",
                                        icon=ft.icons.BUILD,
                                        on_click=lambda e: print("ツール1が選択されました"),
                                    ),
                                    ElevatedButton(
                                        text="ツール2",
                                        icon=ft.icons.SETTINGS,
                                        on_click=lambda e: print("ツール2が選択されました"),
                                    ),
                                    ElevatedButton(
                                        text="Hexファイル検索",
                                        icon=ft.icons.SEARCH,
                                        on_click=navigate_to_hex_tab,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=20,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        spacing=20,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=20,
                ),
            ),
            Tab(
                text="ツール1",
                icon=ft.icons.BUILD,
                content=Container(
                    content=Column(
                        controls=[
                            Text("ツール1の機能", size=20),
                            Text("ここにツール1の機能を実装します"),
                            TextField(label="入力欄", hint_text="ここに入力してください"),
                            ElevatedButton(text="実行", on_click=lambda e: print("実行されました")),
                        ],
                        spacing=20,
                    ),
                    padding=20,
                ),
            ),
            Tab(
                text="ツール2",
                icon=ft.icons.SETTINGS,
                content=Container(
                    content=Column(
                        controls=[
                            Text("ツール2の機能", size=20),
                            Text("ここにツール2の機能を実装します"),
                            Dropdown(
                                width=200,
                                options=[
                                    dropdown.Option("オプション1"),
                                    dropdown.Option("オプション2"),
                                    dropdown.Option("オプション3"),
                                ],
                            ),
                            ElevatedButton(text="適用", on_click=lambda e: print("適用されました")),
                        ],
                        spacing=20,
                    ),
                    padding=20,
                ),
            ),
            # Hexファイル検索ツールのタブ
            Tab(
                text="Hexファイル検索",
                icon=ft.icons.SEARCH,
                content=Container(
                    content=Column(
                        controls=[
                            Text("マイコンファームウェア Hexファイル検索ツール", size=20, weight="bold"),
                            Text("Hexファイルをドラッグ＆ドロップするか、コピー＆ペーストして検索できます"),
                            
                            # ファイル操作エリア
                            Container(
                                content=Row(
                                    controls=[
                                        ElevatedButton(
                                            "ファイルを開く",
                                            icon=ft.icons.FOLDER_OPEN,
                                            on_click=lambda _: file_picker.pick_files(
                                                allow_multiple=False,
                                                file_type=ft.FilePickerFileType.ANY,
                                            ),
                                        ),
                                        TextButton(
                                            "クリア",
                                            icon=ft.icons.CLEAR,
                                            on_click=clear_hex_content,
                                        ),
                                        Text(ref=file_path_text, visible=False),
                                    ],
                                    alignment=ft.MainAxisAlignment.START,
                                ),
                                margin=ft.margin.only(bottom=10),
                            ),
                            
                            # ドラッグ＆ドロップエリア
                            DragTarget(
                                content=Container(
                                    content=Column(
                                        controls=[
                                            Text("ここにHexファイルをドロップ", size=16),
                                            Icon(ft.icons.UPLOAD_FILE, size=30),
                                        ],
                                        spacing=10,
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    ),
                                    alignment=ft.alignment.center,
                                    width=800,
                                    height=100,
                                    border=ft.border.all(2, ft.colors.BLUE_400),
                                    border_radius=10,
                                    bgcolor=ft.colors.BLUE_50,
                                ),
                                on_accept=process_drop_files,
                            ),
                            
                            # Hexコンテンツテキストエリア
                            TextField(
                                ref=hex_content,
                                label="Hexファイルコンテンツ",
                                multiline=True,
                                min_lines=5,
                                max_lines=5,
                                hint_text="ここにHexファイルの内容をコピー＆ペースト、またはファイルを読み込んでください",
                                expand=True,
                                text_size=14,
                            ),
                            
                            # 検索設定
                            ResponsiveRow(
                                controls=[
                                    Column(
                                        controls=[
                                            TextField(
                                                ref=search_query,
                                                label="検索文字列",
                                                hint_text="検索したい文字列または0x始まりのHex値",
                                                prefix_icon=ft.icons.SEARCH,
                                                expand=True,
                                            ),
                                        ],
                                        col={"sm": 6},
                                    ),
                                    Column(
                                        controls=[
                                            Row(
                                                controls=[
                                                    Checkbox(
                                                        ref=hex_ignore_case,
                                                        label="大文字/小文字を区別しない",
                                                        value=True,
                                                    ),
                                                    Checkbox(
                                                        ref=is_binary_search,
                                                        label="バイナリ検索モード",
                                                        tooltip="ASCII文字列または0x始まりのHex値で検索",
                                                        value=False,
                                                    ),
                                                ]
                                            ),
                                        ],
                                        col={"sm": 6},
                                    ),
                                ]
                            ),
                            
                            ResponsiveRow(
                                controls=[
                                    Column(
                                        controls=[
                                            Row(
                                                controls=[
                                                    Text("表示する前後の行数:"),
                                                    TextField(
                                                        ref=context_lines,
                                                        value="5",
                                                        width=60,
                                                        text_align=ft.TextAlign.RIGHT,
                                                        keyboard_type=ft.KeyboardType.NUMBER,
                                                    ),
                                                    ElevatedButton(
                                                        text="検索",
                                                        icon=ft.icons.SEARCH,
                                                        on_click=search_hex_file,
                                                    ),
                                                ],
                                                alignment=ft.MainAxisAlignment.START,
                                            ),
                                        ],
                                        col={"sm": 12},
                                    ),
                                ]
                            ),
                            
                            # 進捗バー
                            ProgressBar(ref=search_progress, visible=False, width=800),
                            
                            # 検索結果
                            Text(ref=search_status, visible=False),
                            
                            Container(
                                content=ListView(
                                    ref=result_view,
                                    spacing=5,
                                    padding=10,
                                    auto_scroll=False,
                                ),
                                bgcolor=ft.colors.WHITE,
                                border=ft.border.all(1, ft.colors.GREY_400),
                                border_radius=5,
                                padding=10,
                                height=300,
                                expand=True,
                            ),
                        ],
                        spacing=10,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    padding=20,
                ),
            ),
        ],
        on_change=on_tab_change,
        expand=True,
    )

    # メインコンテンツ
    page.add(
        tabs,
    )


if __name__ == "__main__":
    ft.app(target=main)
