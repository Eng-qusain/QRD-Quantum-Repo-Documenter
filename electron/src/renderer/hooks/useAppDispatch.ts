// hooks/useAppDispatch.ts
import { useDispatch } from 'react-redux';
import type { AppDispatch } from '../store/store';
export const useAppDispatch = () => useDispatch<AppDispatch>();

// hooks/useAppSelector.ts  — re-export in same file for brevity
export { useAppSelector } from './useAppSelector';
