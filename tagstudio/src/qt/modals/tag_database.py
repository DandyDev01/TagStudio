# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from src.core.library import Library, Tag
from src.core.library.alchemy.enums import FilterState
from src.qt.modals.build_tag import BuildTagPanel
from src.qt.widgets.panel import PanelModal, PanelWidget
from src.qt.widgets.tag import TagWidget


class TagDatabasePanel(PanelWidget):
    tag_chosen = Signal(int)

    def __init__(self, library: Library):
        super().__init__()
        self.lib: Library = library
        self.first_tag_id = -1
        self.tag_limit = 30

        self.setMinimumSize(300, 400)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)

        self.search_field = QLineEdit()
        self.search_field.setObjectName("searchField")
        self.search_field.setMinimumSize(QSize(0, 32))
        self.search_field.setPlaceholderText("Search Tags")
        self.search_field.textEdited.connect(lambda: self.update_tags(self.search_field.text()))
        self.search_field.returnPressed.connect(
            lambda checked=False: self.on_return(self.search_field.text())
        )

        self.scroll_contents = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setContentsMargins(6, 0, 6, 0)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area = QScrollArea()
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidget(self.scroll_contents)

        self.create_tag_button = QPushButton()
        self.create_tag_button.setText("Create Tag")
        self.create_tag_button.clicked.connect(lambda: self.build_tag())

        self.root_layout.addWidget(self.search_field)
        self.root_layout.addWidget(self.scroll_area)
        self.root_layout.addWidget(self.create_tag_button)
        self.update_tags()

    def build_tag(self):
        self.modal = PanelModal(
            BuildTagPanel(self.lib),
            "New Tag",
            "Add Tag",
            has_save=True,
        )

        panel: BuildTagPanel = self.modal.widget
        self.modal.saved.connect(
            lambda: (
                self.lib.add_tag(panel.build_tag(), panel.subtags),
                self.modal.hide(),
                self.update_tags()
            )
        )
        self.modal.show()

    def on_return(self, text: str):
        if text and self.first_tag_id >= 0:
            # callback(self.first_tag_id)
            self.search_field.setText("")
            self.update_tags()
        else:
            self.search_field.setFocus()
            self.parentWidget().hide()

    def update_tags(self, query: str | None = None):
        # TODO: Look at recycling rather than deleting and re-initializing
        while self.scroll_layout.itemAt(0):
            self.scroll_layout.takeAt(0).widget().deleteLater()

        tags = self.lib.search_tags(FilterState(path=query, page_size=self.tag_limit))

        for tag in tags:
            container = QWidget()
            row = QHBoxLayout(container)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(3)
            tag_widget = TagWidget(tag, has_edit=True, has_remove=True)
            tag_widget.on_edit.connect(lambda checked=False, t=tag: self.edit_tag(t))
            tag_widget.on_remove.connect(
                lambda: self.remove_tag(tag))
            row.addWidget(tag_widget)
            self.scroll_layout.addWidget(container)

        self.search_field.setFocus()

    def remove_tag(self, tag: Tag):
        self.lib.remove_tag(tag)
        self.update_tags()

    def edit_tag(self, tag: Tag):
        build_tag_panel = BuildTagPanel(self.lib, tag=tag)

        self.edit_modal = PanelModal(
            build_tag_panel,
            tag.name,
            "Edit Tag",
            done_callback=(self.update_tags(self.search_field.text())),
            has_save=True,
        )
        # TODO Check Warning: Expected type 'BuildTagPanel', got 'PanelWidget' instead
        self.edit_modal.saved.connect(lambda: self.edit_tag_callback(build_tag_panel))
        self.edit_modal.show()

    def edit_tag_callback(self, btp: BuildTagPanel):
        self.lib.add_tag(btp.build_tag())
        self.update_tags(self.search_field.text())
