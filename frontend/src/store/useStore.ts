import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: number;
  email: string;
  full_name?: string;
  avatar_url?: string;
  roles: Array<{ name: string }>;
  is_superuser: boolean;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  logout: () => void;
  updateUser: (user: User) => void;
}

interface UIState {
  sidebarOpen: boolean;
  darkMode: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  toggleDarkMode: () => void;
  setDarkMode: (dark: boolean) => void;
}

interface FilterState {
  userFilters: {
    search?: string;
    role?: string;
    is_active?: boolean;
    skip: number;
    limit: number;
  };
  productFilters: {
    search?: string;
    status?: string;
    category_id?: number;
    is_featured?: boolean;
    is_digital?: boolean;
    min_price?: number;
    max_price?: number;
    in_stock?: boolean;
    skip: number;
    limit: number;
  };
  orderFilters: {
    search?: string;
    status?: string;
    payment_status?: string;
    customer_id?: number;
    date_from?: string;
    date_to?: string;
    skip: number;
    limit: number;
  };
  setUserFilters: (filters: Partial<FilterState['userFilters']>) => void;
  setProductFilters: (filters: Partial<FilterState['productFilters']>) => void;
  setOrderFilters: (filters: Partial<FilterState['orderFilters']>) => void;
  resetFilters: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      setAuth: (user, accessToken, refreshToken) =>
        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: true,
        }),
      logout: () =>
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        }),
      updateUser: (user) => set({ user }),
    }),
    {
      name: 'auth-storage',
    }
  )
);

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      darkMode: false,
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),
      setDarkMode: (dark) => set({ darkMode: dark }),
    }),
    {
      name: 'ui-storage',
    }
  )
);

export const useFilterStore = create<FilterState>((set) => ({
  userFilters: { skip: 0, limit: 100 },
  productFilters: { skip: 0, limit: 100 },
  orderFilters: { skip: 0, limit: 100 },
  setUserFilters: (filters) =>
    set((state) => ({
      userFilters: { ...state.userFilters, ...filters },
    })),
  setProductFilters: (filters) =>
    set((state) => ({
      productFilters: { ...state.productFilters, ...filters },
    })),
  setOrderFilters: (filters) =>
    set((state) => ({
      orderFilters: { ...state.orderFilters, ...filters },
    })),
  resetFilters: () =>
    set({
      userFilters: { skip: 0, limit: 100 },
      productFilters: { skip: 0, limit: 100 },
      orderFilters: { skip: 0, limit: 100 },
    }),
}));
