import { useCallback } from "react";
import toast from "react-hot-toast";
import { apiService } from "../services/api";
import { useAsync } from "../hooks/useAsync";
import { usePolling } from "../hooks/usePolling";
import { dateTime } from "../utils/formatters";
import PageHeader from "../components/common/PageHeader";
import LoadingState from "../components/common/LoadingState";
import ErrorState from "../components/common/ErrorState";

export default function NotificationsPage() {
  const { data, loading, error, execute, setData } = useAsync(async () => apiService.getMyNotifications(), []);

  const refresh = useCallback(() => {
    execute().catch(() => {});
  }, [execute]);

  usePolling(refresh, 10000, true);

  const markRead = async (notificationId) => {
    try {
      await apiService.markNotificationRead(notificationId, true);
      setData((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          notifications: (prev.notifications || []).map((row) =>
            row.notification_id === notificationId ? { ...row, read: true } : row
          ),
        };
      });
      toast.success("Notification marked as read");
    } catch (err) {
      toast.error(err.message || "Unable to update notification");
    }
  };

  if (loading) return <LoadingState label="Loading notifications..." />;
  if (error) return <ErrorState error={error} onRetry={refresh} />;

  const notifications = data?.notifications || [];
  const unreadCount = notifications.filter((row) => !row.read).length;

  return (
    <div className="space-y-5">
      <PageHeader
        title="My Notifications"
        subtitle="Security alerts generated from your account activity"
        action={
          <button type="button" className="btn-secondary" onClick={refresh}>
            Refresh
          </button>
        }
      />

      <div className="card p-4">
        <p className="text-sm text-muted">
          Total: <span className="text-ink">{notifications.length}</span> | Unread: <span className="text-ink">{unreadCount}</span>
        </p>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-900/80 text-left text-xs uppercase tracking-[0.14em] text-muted">
              <tr>
                <th className="px-4 py-3">Severity</th>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Message</th>
                <th className="px-4 py-3">Created</th>
                <th className="px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {notifications.length === 0 ? (
                <tr>
                  <td className="px-4 py-4 text-muted" colSpan={5}>
                    No account notifications yet.
                  </td>
                </tr>
              ) : (
                notifications.map((item) => {
                  const high = String(item.severity || "").toUpperCase() === "HIGH";
                  return (
                    <tr key={item.notification_id} className={["border-t border-slate-800/80", item.read ? "opacity-70" : ""].join(" ")}>
                      <td className="px-4 py-3">
                        <span className={["rounded-full px-2 py-1 text-xs font-semibold", high ? "bg-red-500/20 text-red-300" : "bg-amber-400/20 text-amber-300"].join(" ")}>
                          {String(item.severity || "MEDIUM").toUpperCase()}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-100">{item.title}</td>
                      <td className="px-4 py-3 text-slate-300">{item.message}</td>
                      <td className="px-4 py-3 text-slate-400">{dateTime(item.created_at)}</td>
                      <td className="px-4 py-3">
                        <button
                          type="button"
                          className="btn-secondary px-3 py-1 text-xs"
                          onClick={() => markRead(item.notification_id)}
                          disabled={Boolean(item.read)}
                        >
                          {item.read ? "Read" : "Mark read"}
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
