import { PGlite } from '@electric-sql/pglite';
import { readFile, writeFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
const root = new URL('../', import.meta.url);
const input = JSON.parse(await readFile(new URL('evidence/etl-transform.json', root)));
const db = new PGlite(); // Real PostgreSQL engine, locally embedded as WebAssembly.
await db.exec(await readFile(new URL('etl/schema.sql', root), 'utf8'));
const upsert = `INSERT INTO orders VALUES ($1,$2,$3,$4,$5)
ON CONFLICT (order_id) DO UPDATE SET
order_date=EXCLUDED.order_date,channel=EXCLUDED.channel,
amount=EXCLUDED.amount,currency=EXCLUDED.currency`;
async function load() {
  await db.transaction(async tx => {
    for (const r of input.clean_rows)
      await tx.query(upsert, [r.order_id, r.date, r.channel, r.amount, r.currency]);
  });
}
await load();
const first = (await db.query('SELECT * FROM orders ORDER BY order_id')).rows;
await load();
const second = (await db.query('SELECT * FROM orders ORDER BY order_id')).rows;
assert.deepEqual(second, first, 'Re-running the same batch must preserve the table');
assert.equal(second.length, 8);
const totals = (await db.query('SELECT * FROM revenue_by_channel ORDER BY channel')).rows;
const sourceCents = input.clean_rows.reduce((n,r) => n + Math.round(Number(r.amount)*100),0);
const reportCents = totals.reduce((n,r) => n + Math.round(Number(r.revenue)*100),0);
assert.equal(sourceCents, reportCents);
// Check rollback actually protects an otherwise valid write when a later row fails.
await assert.rejects(db.transaction(async tx => {
  await tx.query(upsert, ['ROLLBACK-TEST','2026-10-05','organic','10.00','USD']);
  await tx.query(upsert, ['BAD-TEST','2026-10-05','organic','-1.00','USD']);
}));
assert.equal((await db.query('SELECT count(*)::int AS n FROM orders')).rows[0].n, 8);
const result = {
  mode: 'Synthetic data; local PostgreSQL via PGlite; no external service calls',
  sourceRows: 12, rejectedRows: 3, duplicateRowsResolved: 1,
  firstRunRows: first.length, secondRunRows: second.length,
  totals, totalRevenue: (sourceCents/100).toFixed(2), currency: 'USD',
  checks: {repeatRunIdentical:true,reportReconciles:true,transactionRollback:true},
  rows: second
};
await writeFile(new URL('evidence/etl-run.json',root),JSON.stringify(result,null,2)+'\n');
await db.close();
console.log('PASS: 8 -> 8 rows after rerun; totals reconcile; failed batch rolled back.');
