import React from 'react';
import Header from './Header';

const Layout = ({ children }) => {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />
      <main className="flex-grow max-w-7xl w-full mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {children}
      </main>
      <footer className="bg-white shadow-inner p-4 text-center text-gray-500 text-sm">
        Literature Review Assistant © {new Date().getFullYear()}
      </footer>
    </div>
  );
};

export default Layout;