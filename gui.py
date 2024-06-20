import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDropEvent,QPixmap, QPainter, QFont, QColor,QFontMetrics,QIcon,QDragEnterEvent
import os
from ncmdump import dump

class DragDropWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("NCM转换器")
        self.setGeometry(100, 100, 400, 400)  # 调整窗体尺寸

        self.setWindowIcon(QIcon(self.get_resource_path("file/favicon-32x32.png")))
        # 加载图片
        self.original_pixmap = QPixmap(self.get_resource_path("file/bk.png"))

        self.label = QLabel(self)
        self.label.setGeometry(0, 0, 400, 400)  # 调整标签尺寸
        self.update_text('将ncm文件拖拽到此处')  # 初始文本内容
    def create_base_pixmap(self):
        """创建不包含文本的基础背景图片"""
        self.base_pixmap = QPixmap(self.get_resource_path("file/bk.png"))
        self.label = QLabel(self)
        self.label.setPixmap(self.base_pixmap)
        self.label.setGeometry(0, 0, 573, 573)
        
    def update_text(self, text):
        resized_pixmap = self.original_pixmap.scaled(self.label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        pixmap = resized_pixmap.copy()  # 复制调整大小后的 QPixmap 对象
        painter = QPainter(pixmap)
        painter.setPen(QColor('black'))  # 设置文本颜色
        font = QFont('SimHei', 20)  # 设置字体和大小
        painter.setFont(font)

        font_metrics = QFontMetrics(font)
        text_width = font_metrics.horizontalAdvance(text)
        text_height = font_metrics.height()

        x = (pixmap.width() - text_width) // 2
        y = (pixmap.height() - text_height) // 2 + font_metrics.ascent()

        painter.drawText(x, y, text)  # 在图片中居中绘制文本
        painter.end()
        self.label.setPixmap(pixmap)  # 更新 QLabel 中的图片

    def get_resource_path(self,relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)


    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        file_paths = [url.toLocalFile() for url in event.mimeData().urls() if url.toLocalFile().endswith(".ncm")]
        if file_paths:
            for file_path in file_paths:
                try:
                    dump(file_path)
                    file_name = os.path.basename(file_path)
                    self.update_text(f"处理完成：{file_name}")
                    QApplication.processEvents()  
                except Exception as e:
                    file_name = os.path.basename(file_path)
                    self.update_text(f"处理文件时出错：{file_name}: {str(e)}")
                    QApplication.processEvents()  
        else:
            self.update_text("没有找到 .ncm 文件")
                    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = DragDropWidget()
    widget.show()
    sys.exit(app.exec())
