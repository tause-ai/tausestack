// Componente cliente ejemplo
'use client';
import React, { useState } from "react";

const Dashboard: React.FC = () => {
  const [count, setCount] = useState(0);
  return (
    <div>
      <h1>Dashboard (Cliente)</h1>
      <button className="btn" onClick={() => setCount(count + 1)}>
        Incrementar: {count}
      </button>
    </div>
  );
};

export default Dashboard;
