import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import LoginForm from '../components/auth/LoginForm';
import SignupForm from '../components/auth/SignupForm';
import Layout from '../components/shared/Layout';

const Login = () => {
  const [isLogin, setIsLogin] = useState(true);

  const toggleForm = () => {
    setIsLogin(!isLogin);
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-extrabold text-gray-900">Literature Review Assistant</h1>
          <p className="mt-2 text-sm text-gray-600">
            Automate your systematic literature review process
          </p>
        </div>

        {isLogin ? (
          <LoginForm />
        ) : (
          <SignupForm />
        )}

        <div className="text-center mt-4">
          <button
            onClick={toggleForm}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;