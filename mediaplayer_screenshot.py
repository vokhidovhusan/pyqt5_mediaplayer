
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import (
    QMediaContent,
    QMediaPlayer,
    QVideoFrame,
    QMediaPlaylist,
    QVideoProbe,
    )
from PyQt5.QtMultimediaWidgets import QVideoWidget

from MainWindow import Ui_MainWindow
# from MainWindowMediaPlayer import Ui_MainWindow

def hhmmss(ms):
    # s = 1000
    # m = 60000
    # h = 36000
    h, r = divmod(ms, 36000)
    m, r = divmod(r, 60000)
    s, _ = divmod(r, 1000)
    return ("%d:%02d:%02d" % (h,m,s)) if h else ("%d:%02d" % (m,s))

class PlaylistModel(QAbstractListModel):
    def __init__(self, playlist, *args, **kwargs):
        super(PlaylistModel, self).__init__(*args, **kwargs)
        self.playlist = playlist

    def data(self, index, role):
        if role == Qt.DisplayRole:
            media = self.playlist.media(index.row())
            return media.canonicalUrl().fileName()

    def rowCount(self, index):
        return self.playlist.mediaCount()

class Worker(QRunnable):
    def __init__(self, frame):
        super().__init__()
        self.frame = frame

    @pyqtSlot()
    def run(self):        
        
        self.process_frame(self.frame)

    def process_frame(self, frame):
        # Save image here
        self.path = './screenshots/'
        str_time = QTime.currentTime().toString("hh:mm:ss.zzz")
        filename = self.path+'/{}_{}.png'.format('screenshot', str_time)
        image = frame.image()
        image.save(filename)
        

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.threadpool = QThreadPool()
        print(
            'Multithreading with maximum %d threads' % self.threadpool.maxThreadCount()
        )

        self.player = QMediaPlayer()

        # Setup the playlist.        
        self.playlist = QMediaPlaylist()
        self.player.setPlaylist(self.playlist)


        # Setup the player
        self.player.durationChanged.connect(self.update_duration)
        self.player.positionChanged.connect(self.update_position)
        self.playlist.currentIndexChanged.connect(self.playlist_position_changed)
        self.player.error.connect(self.erroralert)
        self.videoWidget = QVideoWidget()       
        self.player.setVideoOutput(self.videoWidget)
        

        self.model = PlaylistModel(self.playlist)
        self.playListView.setModel(self.model)
        selection_model = self.playListView.selectionModel()        
        selection_model.selectionChanged.connect(self.playlist_selection_changed)

        self.currentFrame = QVideoFrame()

        # Connect control buttons/slides for media player.
        self.playButton.pressed.connect(self.player.play)
        self.pauseButton.pressed.connect(self.player.pause)
        self.stopButton.pressed.connect(self.player.stop)        
        
        layout = QVBoxLayout()
        layout.addWidget(self.videoWidget)
        self.viewWidget.setLayout(layout)

        self.probe = QVideoProbe()        
        self.probe.videoFrameProbed.connect(self.on_videoFrameProbed)        
        self.probe.setSource(self.player)
        
        self.timeSlider.valueChanged.connect(self.player.setPosition)

        self.open_file_action.triggered.connect(self.open_file)

        # button for save current frame
        self.saveButton.pressed.connect(self.save_frame)

        self.setAcceptDrops(True)

        self.show()

    
    def on_videoFrameProbed(self, frame):
        self.frame = frame
        

    def save_frame(self):                
        worker = Worker(self.frame)
        self.threadpool.start(worker)
        


    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        for url in e.mimeData().urls():
            self.playlist.addMedia(
                QMediaContent(url)
            )

        self.model.layoutChanged.emit()

        # If not playing, seeking to first of newly added + play.
        if self.player.state() != QMediaPlayer.PlayingState:
            i = self.playlist.mediaCount() - len(e.mimeData().urls())
            self.playlist.setCurrentIndex(i)
            self.player.play()

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open file", "", "mp3 Audio (*.mp3);mp4 Video (*.mp4);Movie files (*.mov);All files (*.*)")
    
        if path:
            self.playlist.addMedia(
                QMediaContent(
                    QUrl.fromLocalFile(path)
                )
            )

        self.model.layoutChanged.emit()

    def update_duration(self, duration):
        print("!", duration)
        print("?", self.player.duration())
        
        self.timeSlider.setMaximum(duration)

        if duration >= 0:
            self.totalTimeLabel.setText(hhmmss(duration))

    def update_position(self, position):
        if position >= 0:
            self.currentTimeLabel.setText(hhmmss(position))

        # Disable the events to prevent updating triggering a setPosition event (can cause stuttering).
        self.timeSlider.blockSignals(True)
        self.timeSlider.setValue(position)
        self.timeSlider.blockSignals(False)

    def playlist_selection_changed(self, ix):
        # We receive a QItemSelection from selectionChanged.
        i = ix.indexes()[0].row()
        self.playlist.setCurrentIndex(i)

    def playlist_position_changed(self, i):
        if i > -1:
            ix = self.model.index(i)
            self.playListView.setCurrentIndex(ix)
            # self.playlistView.setCurrentIndex(ix)

    def erroralert(self, *args):
        print(args)




if __name__ == '__main__':
    app = QApplication([])
    app.setApplicationName("Failamp")
    app.setStyle("Fusion")

    # Fusion dark palette from https://gist.github.com/QuantumCD/6245215.
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")

    window = MainWindow()
    app.exec_()