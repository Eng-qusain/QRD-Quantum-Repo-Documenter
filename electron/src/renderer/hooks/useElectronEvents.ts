import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch } from './useAppDispatch';
import { toggleTheme, setUpdateAvailable, setUpdateDownloaded } from '../store/slices/uiSlice';
import { setProjectPath, scanProject } from '../store/slices/projectSlice';
import { addNotification } from '../store/slices/uiSlice';

export const useElectronEvents = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  useEffect(() => {
    if (!window.electron) return;

    const removers = [
      window.electron.on('menu:toggle-theme', () => dispatch(toggleTheme())),
      window.electron.on('menu:open-project', async () => {
        const p = await window.electron?.openDirectory();
        if (p) {
          dispatch(setProjectPath(p));
          navigate('/dashboard');
        }
      }),
      window.electron.on('menu:export-single', () => navigate('/export')),
      window.electron.on('menu:export-package', () => navigate('/export')),
      window.electron.on('menu:open-recent', async (path: unknown) => {
        dispatch(setProjectPath(path as string));
        navigate('/dashboard');
      }),
      window.electron.on('updater:update-available', () => dispatch(setUpdateAvailable(true))),
      window.electron.on('updater:update-downloaded', () => dispatch(setUpdateDownloaded(true))),
    ];

    return () => removers.forEach((r) => typeof r === 'function' && r());
  }, [dispatch, navigate]);
};
