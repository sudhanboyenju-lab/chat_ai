import { useEffect, useState } from "react";
import { api } from "../api";

const emptyForm = {
  item_id: "",
  dish_name: "",
  price: "",
  category: "",
  spice_level: "",
  ingredients: "",
};

export default function AdminPanel() {
  const [items, setItems] = useState({});
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const result = await api.listMenuItems();
      setItems(result.menu_items || {});
    } catch (err) {
      setStatus(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const startEdit = (itemId, data) => {
    setEditingId(itemId);
    setForm({
      item_id: itemId,
      dish_name: data.dish_name || "",
      price: data.price || "",
      category: data.category || "",
      spice_level: data.spice_level || "",
      ingredients: (data.documents || []).join(", "),
    });
  };

  const resetForm = () => {
    setEditingId(null);
    setForm(emptyForm);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("");
    const payload = {
      dish_name: form.dish_name,
      price: form.price,
      category: form.category,
      spice_level: form.spice_level,
      ingredients: form.ingredients
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
    };

    try {
      if (editingId) {
        await api.updateMenuItem(editingId, payload);
        setStatus(`Updated ${form.dish_name}.`);
      } else {
        await api.addMenuItem({ item_id: form.item_id, ...payload });
        setStatus(`Added ${form.dish_name}.`);
      }
      resetForm();
      load();
    } catch (err) {
      setStatus(err.message);
    }
  };

  const handleDelete = async (itemId, name) => {
    if (!window.confirm(`Remove ${name} from the menu?`)) return;
    try {
      await api.deleteMenuItem(itemId);
      setStatus(`Removed ${name}.`);
      load();
    } catch (err) {
      setStatus(err.message);
    }
  };

  return (
    <div className="admin-panel">
      <section className="admin-form-section">
        <h2>{editingId ? "Edit dish" : "Add a dish"}</h2>
        <form onSubmit={handleSubmit} className="admin-form">
          <label>
            Item ID
            <input
              value={form.item_id}
              onChange={(e) => setForm({ ...form, item_id: e.target.value })}
              disabled={!!editingId}
              required
            />
          </label>
          <label>
            Dish name
            <input
              value={form.dish_name}
              onChange={(e) => setForm({ ...form, dish_name: e.target.value })}
              required
            />
          </label>
          <label>
            Price
            <input
              value={form.price}
              onChange={(e) => setForm({ ...form, price: e.target.value })}
              required
            />
          </label>
          <label>
            Category
            <input
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
            />
          </label>
          <label>
            Spice level
            <input
              value={form.spice_level}
              onChange={(e) => setForm({ ...form, spice_level: e.target.value })}
            />
          </label>
          <label className="full-width">
            Ingredients (comma separated)
            <input
              value={form.ingredients}
              onChange={(e) => setForm({ ...form, ingredients: e.target.value })}
            />
          </label>

          <div className="admin-form-actions">
            <button type="submit" className="primary-btn">
              {editingId ? "Save changes" : "Add dish"}
            </button>
            {editingId && (
              <button type="button" className="text-btn" onClick={resetForm}>
                Cancel
              </button>
            )}
          </div>
        </form>
        {status && <p className="admin-status">{status}</p>}
      </section>

      <section className="admin-table-section">
        <h2>Current menu</h2>
        {loading ? (
          <p>Loading…</p>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>Dish</th>
                <th>Price</th>
                <th>Category</th>
                <th>Spice</th>
                <th>Ingredients</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(items).map(([itemId, data]) => (
                <tr key={itemId}>
                  <td>{data.dish_name}</td>
                  <td>{data.price}</td>
                  <td>{data.category}</td>
                  <td>{data.spice_level}</td>
                  <td>{(data.documents || []).join(", ")}</td>
                  <td className="row-actions">
                    <button className="text-btn" onClick={() => startEdit(itemId, data)}>
                      Edit
                    </button>
                    <button
                      className="text-btn danger"
                      onClick={() => handleDelete(itemId, data.dish_name)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
