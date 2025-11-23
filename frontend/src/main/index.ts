import { app, shell, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'
import { spawn } from 'child_process'

// Path to backend relative to workspace root
// In development: out/main/index.js -> ../../.. gets to workspace root
// Adjust path calculation based on whether we're in dev or production
const backendPath = is.dev 
  ? join(__dirname, '../../../backend')
  : join(process.resourcesPath, 'backend')

const managePyPath = join(backendPath, 'manage.py')
const venvPython = join(__dirname, '../../../.venv/Scripts/python.exe')

let backendProcess: ReturnType<typeof spawn> | null = null

function startBackend(): void {
  // Use venv python if it exists, otherwise fall back to system python
  const pythonCmd = is.dev ? venvPython : 'python'
  
  console.log(`Starting Django backend from: ${managePyPath}`)
  
  backendProcess = spawn(pythonCmd, [managePyPath, 'runserver', '127.0.0.1:8811'], {
    cwd: backendPath,
    stdio: 'inherit',
    shell: true,
    env: {
      ...process.env,
      PYTHONUNBUFFERED: '1'
    }
  })

  backendProcess.on('error', (err) => {
    console.error('Failed to start backend process:', err)
  })

  backendProcess.on('exit', (code) => {
    console.log(`Backend process exited with code ${code}`)
  })
}


function createWindow(): void {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 900,
    height: 670,
    show: false,
    autoHideMenuBar: true,
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // HMR for renderer base on electron-vite cli.
  // Load the remote URL for development or the local html file for production.
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(() => {
  // Start the Django backend
  startBackend()
  
  // Set app user model id for windows
  electronApp.setAppUserModelId('com.electron')

  // Default open or close DevTools by F12 in development
  // and ignore CommandOrControl + R in production.
  // see https://github.com/alex8088/electron-toolkit/tree/master/packages/utils
  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  // IPC test
  ipcMain.on('ping', () => console.log('pong'))

  // Handle file open requests from renderer
  ipcMain.handle('open-file', async (_event, filePath: string) => {
    try {
      const result = await shell.openPath(filePath)
      return result // empty string on success, error message on failure
    } catch (error) {
      return `Failed to open file: ${error}`
    }
  })

  createWindow()

  app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  // Kill backend process when app closes
  if (backendProcess) {
    backendProcess.kill()
  }
  
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// Ensure backend process is killed when app quits (covers Cmd+Q, force quit, etc.)
app.on('before-quit', () => {
  if (backendProcess) {
    console.log('Shutting down backend process...')
    backendProcess.kill('SIGTERM')
  }
})

// Handle cleanup on unexpected exits
process.on('exit', () => {
  if (backendProcess) {
    backendProcess.kill('SIGKILL')
  }
})

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here.
