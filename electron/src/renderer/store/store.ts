import { configureStore } from '@reduxjs/toolkit';
import uiReducer from './slices/uiSlice';
import projectReducer from './slices/projectSlice';
import exportReducer from './slices/exportSlice';
import scannerReducer from './slices/scannerSlice';

export const store = configureStore({
  reducer: {
    ui: uiReducer,
    project: projectReducer,
    export: exportReducer,
    scanner: scannerReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['project/setFiles'],
        ignoredPaths: ['project.fileTree'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
