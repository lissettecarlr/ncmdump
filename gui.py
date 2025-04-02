import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QFileDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDropEvent, QPixmap, QPainter, QFont, QColor, QFontMetrics, QIcon, QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent
import os
from ncmdump import dump

class DragDropWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.is_dragging = False
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("NCM转换器")
        self.setGeometry(100, 100, 400, 400)
        self.setMinimumSize(200, 200) 
        self.setWindowIcon(QIcon(self.get_resource_path("file/favicon-32x32.png")))
        self.background_image = QPixmap(self.get_resource_path("file/bk_M.png"))
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        self.label = QLabel(self)
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        self.scale_factor = 1.0
        self.update_display('将ncm文件拖拽到此处')

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_display(self.label.text())

    def update_display(self, text):
        pixmap = self.create_background()
        
        display_text = text
        if self.is_dragging and text == '将ncm文件拖拽到此处':
            display_text = '释放鼠标以转换文件'
            
        self.draw_text(pixmap, display_text)
        self.label.setPixmap(pixmap)
    
    def create_background(self):
        label_size = self.label.size()
        
        pixmap = QPixmap(label_size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        scaled_size = label_size * self.scale_factor
        scaled_bg = self.background_image.scaled(
            scaled_size.width(), 
            scaled_size.height(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        x_offset = (label_size.width() - scaled_bg.width()) // 2
        y_offset = (label_size.height() - scaled_bg.height()) // 2
        painter.drawPixmap(x_offset, y_offset, scaled_bg)
        
        if self.is_dragging:
            painter.fillRect(pixmap.rect(), QColor(0, 120, 215, 70))
            pen_width = 4
            painter.setPen(QColor(0, 120, 215, 200))
            painter.drawRect(pen_width//2, pen_width//2, 
                           pixmap.width()-pen_width, pixmap.height()-pen_width)
        
        painter.end()
        return pixmap
    
    def draw_text(self, pixmap, text):
        painter = QPainter(pixmap)
        
        font_size = 18
        font = QFont('Microsoft YaHei', font_size)
        font.setBold(True)
        painter.setFont(font)
        font_metrics = QFontMetrics(font)
        
        text_lines = self.prepare_text_lines(text, font_metrics, pixmap.width() - 20)
        
        total_height = len(text_lines) * font_metrics.height()
        current_y = (pixmap.height() - total_height) // 2 + font_metrics.ascent()
        
        for line in text_lines:
            text_width = font_metrics.horizontalAdvance(line)
            x = (pixmap.width() - text_width) // 2
            
            painter.setPen(QColor(0, 0, 0, 160))
            shadow_offset = 2
            painter.drawText(x + shadow_offset, current_y + shadow_offset, line)
            
            painter.setPen(QColor('white'))
            painter.drawText(x, current_y, line)
            
            current_y += font_metrics.height()
            
        painter.end()
    
    def prepare_text_lines(self, text, font_metrics, max_width):
        if font_metrics.horizontalAdvance(text) <= max_width:
            return [text]
            
        text_lines = []
        parts = text.split('：', 1)
        if len(parts) > 1:
            text_lines.append(parts[0] + '：')
            remaining = parts[1]
            
            while remaining:
                i = 0
                while i < len(remaining):
                    if font_metrics.horizontalAdvance(remaining[:i+1]) > max_width:
                        break
                    i += 1
                    
                if i == 0:
                    i = 1
                    
                text_lines.append(remaining[:i])
                remaining = remaining[i:]
        else:
            remaining = text
            while remaining:
                i = 0
                while i < len(remaining):
                    if font_metrics.horizontalAdvance(remaining[:i+1]) > max_width:
                        break
                    i += 1
                    
                if i == 0:
                    i = 1
                    
                text_lines.append(remaining[:i])
                remaining = remaining[i:]
                
        return text_lines

    def get_resource_path(self,relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def set_drag_state(self, is_dragging):
        """统一设置拖拽状态"""
        self.is_dragging = is_dragging
        self.scale_factor = 0.97 if is_dragging else 1.0
        self.update_display('将ncm文件拖拽到此处')

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            has_ncm = False
            for url in event.mimeData().urls():
                if url.toLocalFile().endswith('.ncm'):
                    has_ncm = True
                    break
            
            if has_ncm:
                self.set_drag_state(True)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self.set_drag_state(False)
        event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.select_files()
    
    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择NCM文件",
            "",
            "NCM Files (*.ncm)"
        )
        if files:
            self.process_files(files)
    
    def process_files(self, file_paths):
        ncm_files = [f for f in file_paths if f.endswith('.ncm')]
        if ncm_files:
            success_count = 0
            total_files = len(ncm_files)
            
            for file_path in ncm_files:
                try:
                    dump(file_path)
                    success_count += 1
                    file_name = os.path.basename(file_path)
                    self.update_display(f"处理完成：{file_name}\n已转换：{success_count}/{total_files}")
                    QApplication.processEvents()
                except Exception as e:
                    file_name = os.path.basename(file_path)
                    self.update_display(f"处理文件时出错：{file_name}: {str(e)}\n已转换：{success_count}/{total_files}")
                    QApplication.processEvents()
            
            self.update_display(f"转换完成！\n共转换 {success_count}/{total_files} 个文件")
        else:
            self.update_display("没有找到 .ncm 文件")
    
    def dropEvent(self, event: QDropEvent):
        self.is_dragging = False
        self.scale_factor = 1.0
        self.update_display('处理中...')
        file_paths = [url.toLocalFile() for url in event.mimeData().urls()]
        self.process_files(file_paths)

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().endswith('.ncm'):
                    event.acceptProposedAction()
                    return
        event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = DragDropWidget()
    widget.show()
    sys.exit(app.exec())
