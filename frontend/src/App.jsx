import { Outlet } from 'react-router-dom';

function App() {
  return (
    <main>
      {/* C'est ici que le routeur mettra la page active (LoginPage, etc.) */}
      <Outlet />
    </main>
  );
}

export default App;