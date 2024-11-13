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
        self.setGeometry(100, 100, 400, 400)
        self.setMinimumSize(200, 200) 
        self.setWindowIcon(QIcon(self.get_resource_path("file/favicon-32x32.png")))
        # 加载图片
        self.original_pixmap = QPixmap(self.get_resource_path("file/bk_l.png"))
        
        # 修改标签布局方式
        layout = QVBoxLayout()
        self.label = QLabel(self)
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        self.update_text('将ncm文件拖拽到此处')

    # 添加 resizeEvent 处理函数
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 当窗口大小改变时，更新文本显示
        self.update_text(self.label.text())

    def update_text(self, text):
        resized_pixmap = self.original_pixmap.scaled(self.label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        pixmap = resized_pixmap.copy()
        painter = QPainter(pixmap)
        painter.setPen(QColor('black'))

        # 计算合适的字体大小
        font_size = 16
        max_width = pixmap.width() * 0.9  # 留出10%边距
        font = QFont('SimHei', font_size)
        font_metrics = QFontMetrics(font)
        
        # 如果文本太长，进行截断处理
        text_lines = []
        if len(text) > 30:  # 如果文本长度超过30个字符
            words = text.split('：', 1)  # 在"："处分割
            if len(words) > 1:
                text_lines.append(words[0] + '：')
                remaining_text = words[1]
                # 每行最多显示20个字符
                while remaining_text:
                    if len(remaining_text) > 20:
                        text_lines.append(remaining_text[:20])
                        remaining_text = remaining_text[20:]
                    else:
                        text_lines.append(remaining_text)
                        break
        else:
            text_lines = [text]

        # 绘制多行文本
        painter.setFont(font)
        total_height = len(text_lines) * font_metrics.height()
        current_y = (pixmap.height() - total_height) // 2 + font_metrics.ascent()

        for line in text_lines:
            text_width = font_metrics.horizontalAdvance(line)
            x = (pixmap.width() - text_width) // 2
            painter.drawText(x, current_y, line)
            current_y += font_metrics.height()

        painter.end()
        self.label.setPixmap(pixmap)

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
