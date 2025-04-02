import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QFileDialog
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QDropEvent, QPixmap, QPainter, QFont, QColor, QFontMetrics, QIcon, QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent
import os
from ncmdump import dump

class DragDropWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.is_dragging = False  # 添加拖拽状态标记
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("NCM转换器")
        self.setGeometry(100, 100, 400, 400)
        self.setMinimumSize(200, 200) 
        self.setWindowIcon(QIcon(self.get_resource_path("file/favicon-32x32.png")))
        # 加载图片
        self.original_pixmap = QPixmap(self.get_resource_path("file/bk_l.png"))
        # 添加拖拽时的背景图片
        self.drag_pixmap = self.original_pixmap.copy()  # 创建拖拽状态下的背景图像副本
        
        # 修改标签布局方式
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)  # 设置边距，为高亮边框留出空间
        self.label = QLabel(self)
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        # 创建用于动画效果的缩放因子
        self.scale_factor = 1.0
        
        self.update_text('将ncm文件拖拽到此处')

    # 添加 resizeEvent 处理函数
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 当窗口大小改变时，更新文本显示
        self.update_text(self.label.text())

    def update_text(self, text):
        # 根据当前是否处于拖拽状态选择背景图片
        base_pixmap = self.drag_pixmap if self.is_dragging else self.original_pixmap
        
        # 创建适合标签大小的背景
        label_size = self.label.size()
        # 应用缩放因子，只在视觉上缩放而不改变实际尺寸
        scaled_size = label_size * self.scale_factor
        
        resized_pixmap = base_pixmap.scaled(
            scaled_size.width(), 
            scaled_size.height(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        
        # 创建一个与标签大小相同的空白画布
        pixmap = QPixmap(label_size)
        pixmap.fill(Qt.GlobalColor.transparent)  # 填充透明背景
        
        # 将缩放后的图像绘制到中心位置
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 计算居中位置
        x_offset = (label_size.width() - resized_pixmap.width()) // 2
        y_offset = (label_size.height() - resized_pixmap.height()) // 2
        painter.drawPixmap(x_offset, y_offset, resized_pixmap)
        
        # 如果正在拖拽，绘制半透明叠加层和高亮边框
        if self.is_dragging:
            # 绘制半透明蓝色叠加层
            overlay_color = QColor(0, 120, 215, 70)  # 半透明蓝色
            painter.fillRect(pixmap.rect(), overlay_color)
            
            # 绘制高亮边框
            border_color = QColor(0, 120, 215, 200)  # 蓝色边框
            pen_width = 4
            painter.setPen(QColor(border_color))
            painter.drawRect(pen_width//2, pen_width//2, 
                           pixmap.width()-pen_width, pixmap.height()-pen_width)
            
            # 如果是拖拽状态，修改提示文本
            if text == '将ncm文件拖拽到此处':
                text = '释放鼠标以转换文件'

        # 调整字体设置
        font_size = 18  # 增大字号
        font = QFont('Microsoft YaHei', font_size)  # 使用微软雅黑字体
        font.setBold(True)  # 设置为粗体
        painter.setFont(font)
        font_metrics = QFontMetrics(font)

        # 文本分行处理保持不变
        text_lines = []
        if len(text) > 30:
            words = text.split('：', 1)
            if len(words) > 1:
                text_lines.append(words[0] + '：')
                remaining_text = words[1]
                while remaining_text:
                    if len(remaining_text) > 20:
                        text_lines.append(remaining_text[:20])
                        remaining_text = remaining_text[20:]
                    else:
                        text_lines.append(remaining_text)
                        break
        else:
            text_lines = [text]

        # 计算文本位置
        total_height = len(text_lines) * font_metrics.height()
        current_y = (pixmap.height() - total_height) // 2 + font_metrics.ascent()

        # 绘制文本阴影和主文本
        for line in text_lines:
            text_width = font_metrics.horizontalAdvance(line)
            x = (pixmap.width() - text_width) // 2
            
            # 绘制阴影
            painter.setPen(QColor(0, 0, 0, 160))  # 半透明黑色阴影
            shadow_offset = 2  # 阴影偏移量
            painter.drawText(x + shadow_offset, current_y + shadow_offset, line)
            
            # 绘制主文本
            painter.setPen(QColor('white'))  # 使用白色作为主文本颜色
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
            # 检查是否有NCM文件
            has_ncm = False
            for url in event.mimeData().urls():
                if url.toLocalFile().endswith('.ncm'):
                    has_ncm = True
                    break
            
            if has_ncm:
                self.is_dragging = True
                # 应用缩放效果，使画面看起来轻微缩小
                self.scale_factor = 0.97
                self.update_text('将ncm文件拖拽到此处')
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self.is_dragging = False
        # 恢复原始大小
        self.scale_factor = 1.0
        self.update_text('将ncm文件拖拽到此处')
        event.accept()

    # 添加鼠标点击事件处理
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.select_files()
    
    # 添加文件选择方法
    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择NCM文件",
            "",
            "NCM Files (*.ncm)"
        )
        if files:
            self.process_files(files)
    
    # 抽取共同的文件处理逻辑
    def process_files(self, file_paths):
        ncm_files = [f for f in file_paths if f.endswith('.ncm')]
        if ncm_files:
            success_count = 0  # 添加成功计数器
            total_files = len(ncm_files)  # 总文件数
            
            for file_path in ncm_files:
                try:
                    dump(file_path)
                    success_count += 1  # 成功转换后计数加1
                    file_name = os.path.basename(file_path)
                    self.update_text(f"处理完成：{file_name}\n已转换：{success_count}/{total_files}")
                    QApplication.processEvents()
                except Exception as e:
                    file_name = os.path.basename(file_path)
                    self.update_text(f"处理文件时出错：{file_name}: {str(e)}\n已转换：{success_count}/{total_files}")
                    QApplication.processEvents()
            
            # 所有文件处理完成后显示最终结果
            self.update_text(f"转换完成！\n共转换 {success_count}/{total_files} 个文件")
        else:
            self.update_text("没有找到 .ncm 文件")
    
    # 修改 dropEvent 方法，使用新的处理逻辑
    def dropEvent(self, event: QDropEvent):
        self.is_dragging = False
        # 恢复原始大小
        self.scale_factor = 1.0
        self.update_text('处理中...')
        file_paths = [url.toLocalFile() for url in event.mimeData().urls()]
        self.process_files(file_paths)

    def dragMoveEvent(self, event: QDragMoveEvent):
        # 保持拖拽状态
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
