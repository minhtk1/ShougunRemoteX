"""
PyInstaller hook để xử lý gi module (PyGObject)
Code copied from xpra-client under GNU General Public License v2.0
"""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect tất cả submodules của gi
hiddenimports = collect_submodules('gi')

# Collect data files từ gi module
datas = collect_data_files('gi')

# Thêm các module cần thiết cho GTK3
hiddenimports.extend([
    'gi.repository.Gtk',
    'gi.repository.Gdk', 
    'gi.repository.GObject',
    'gi.repository.GLib',
    'gi.repository.Gio',
    'gi.repository.Pango',
    'gi.repository.PangoCairo',
    'gi.repository.GdkPixbuf',
    'gi.repository.cairo',
    'gi.overrides',
    'gi.overrides.Gtk',
    'gi.overrides.Gdk',
])

# Thêm cairo module
hiddenimports.extend(collect_submodules('cairo'))
datas.extend(collect_data_files('cairo'))



