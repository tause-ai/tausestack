// Componente de servidor ejemplo
import React from "react";

export interface UserTableProps {
  users: { id: string; name: string }[];
}

/**
 * Tabla de usuarios (componente de servidor)
 */
const UserTable: React.FC<UserTableProps> = ({ users }) => {
  return (
    <table className="w-full border">
      <thead>
        <tr>
          <th>ID</th>
          <th>Nombre</th>
        </tr>
      </thead>
      <tbody>
        {users.map((u) => (
          <tr key={u.id}>
            <td>{u.id}</td>
            <td>{u.name}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default UserTable;
