import { useState } from "react";
import { Login } from "./components/Auth/Login";
import { Register } from "./components/Auth/Register";

function App() {
  const [isLogin, setIsLogin] = useState(true);

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="p-4 flex justify-center space-x-4">
        <button
          className={`px-4 py-2 rounded ${
            isLogin ? "bg-indigo-600 text-white" : "bg-gray-200"
          }`}
          onClick={() => setIsLogin(true)}
        >
          Login
        </button>
        <button
          className={`px-4 py-2 rounded ${
            !isLogin ? "bg-indigo-600 text-white" : "bg-gray-200"
          }`}
          onClick={() => setIsLogin(false)}
        >
          Register
        </button>
      </nav>
      {isLogin ? <Login /> : <Register />}
    </div>
  );
}

export default App;
