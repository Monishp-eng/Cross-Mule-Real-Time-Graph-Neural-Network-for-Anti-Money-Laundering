import { currency, dateTime } from "../../utils/formatters";

export default function TransactionsTable({ transactions = [] }) {
  return (
    <div className="card overflow-hidden shadow-panel">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-700/50 bg-slate-950/35 px-6 py-5">
        <div>
          <h3 className="text-base font-bold uppercase tracking-[0.15em] text-slate-200">Transactions</h3>
          <p className="mt-2 text-sm text-muted">Live transaction feed with status classification and time context.</p>
        </div>
        <p className="rounded-full border border-slate-700/70 bg-slate-900/70 px-4 py-2 text-sm font-semibold text-slate-300 shadow-sm">
          {transactions.length} records
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-base">
          <thead className="bg-slate-900/80 text-left text-sm font-semibold uppercase tracking-[0.15em] text-muted">
            <tr>
              <th className="px-6 py-4">Transaction ID</th>
              <th className="px-6 py-4">User ID</th>
                <th className="px-6 py-4">Name</th>
                <th className="px-6 py-4">Mobile</th>
                <th className="px-6 py-4">Account</th>
                <th className="px-6 py-4">Product</th>
                <th className="px-6 py-4">Receiver</th>
              <th className="px-6 py-4">Amount</th>
                <th className="px-6 py-4">Narration</th>
                <th className="px-6 py-4">Pincode</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {transactions.length === 0 ? (
              <tr>
                  <td className="px-6 py-6 text-center text-muted" colSpan={12}>
                  No transactions match the selected filters.
                </td>
              </tr>
            ) : (
              transactions.map((txn) => {
                const status = String(
                  txn.status_label ||
                    (txn.source_is_fraud ? "FRAUD" : txn.status || txn.decision || "SAFE")
                ).toUpperCase();
                const isFraud =
                  txn.source_is_fraud || status.includes("FRAUD") || status.includes("BLOCK") || status.includes("FLAG");
                const amount = txn.amount ?? txn.transfer_amount ?? txn.source_amount ?? 0;
                const currencyCode = txn.currency || txn.source_currency || "INR";
                const rowKey = `${txn.transaction_id || txn.id || "txn"}-${txn.timestamp || txn.transfer_time || idx}`;
                return (
                  <tr key={rowKey} className="border-t border-slate-800/80 odd:bg-slate-950/20">
                    <td className="px-6 py-4 code text-sm font-medium text-slate-300">{txn.transaction_id || txn.id}</td>
                    <td className="px-6 py-4 font-medium">{txn.user_id || txn.source_account_id || "-"}</td>
                      <td className="px-6 py-4 font-medium text-slate-300">{txn.name || "-"}</td>
                      <td className="px-6 py-4 code text-sm font-medium text-slate-300">{txn.mobile_number || "-"}</td>
                      <td className="px-6 py-4 code text-sm font-medium text-slate-300">{txn.account_number || txn.source_account_id || "-"}</td>
                      <td className="px-6 py-4 text-slate-300">{txn.account_product_type || "-"}</td>
                      <td className="px-6 py-4 code text-sm font-medium text-slate-300">{txn.receiver_id || "-"}</td>
                    <td className="px-6 py-4 font-medium text-slate-200">{currency(amount, currencyCode)}</td>
                      <td className="px-6 py-4 text-sm text-slate-300 leading-relaxed">{txn.narration || "-"}</td>
                      <td className="px-6 py-4 code text-sm font-medium text-slate-300">{txn.pincode || "-"}</td>
                    <td className="px-6 py-4">
                      <span
                        className={[
                          "rounded-full px-3 py-1 text-sm font-bold shadow-sm",
                          isFraud ? "bg-red-500/20 text-red-300" : "bg-emerald-500/20 text-emerald-300",
                        ].join(" ")}
                      >
                        {isFraud ? "Fraud" : "Safe"}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-400">{dateTime(txn.timestamp || txn.transfer_time)}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
