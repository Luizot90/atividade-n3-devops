const http = require('node:http');
const mysql = require('mysql2/promise');
const { createClient } = require('redis');
const env = process.env;
const db = mysql.createPool({
  host: env.DB_HOST, user: env.DB_USER, password: env.DB_PASSWORD,
  database: env.DB_NAME, connectionLimit: 5, connectTimeout: 2000
});
const redis = createClient({
  socket: { host: env.REDIS_HOST, port: Number(env.REDIS_PORT || 6379), connectTimeout: 2000 },
  disableOfflineQueue: true
});
redis.on('error', err => console.error('Redis:', err.message));
redis.connect().catch(err => console.error(err.message));

let schemaReady = false;
async function initialize() {
  try {
    await db.query('CREATE TABLE IF NOT EXISTS jogos (id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT, titulo VARCHAR(100) NOT NULL)');
    schemaReady = true;
  } catch (err) {
    console.error('Inicialização do banco:', err.message);
    setTimeout(initialize, 2000);
  }
}
initialize();

function reply(res, status, data) {
  res.writeHead(status, {'Content-Type': 'application/json; charset=utf-8'});
  res.end(JSON.stringify(data));
}
http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, 'http://localhost');
    if (req.method === 'GET' && url.pathname === '/live') return reply(res, 200, {vivo: true});
    if (req.method === 'GET' && url.pathname === '/') return reply(res, 200, {api: 'Catálogo de jogos', versao: env.APP_VERSION});
    if (!schemaReady) return reply(res, 503, {erro: 'Preparando tabela'});
    if (req.method === 'GET' && url.pathname === '/health') {
      await Promise.all([db.query('SELECT 1'), redis.ping()]);
      return reply(res, 200, {mysql: 'ok', redis: 'ok'});
    }
    if (url.pathname === '/jogos' && req.method === 'POST') {
      const titulo = (url.searchParams.get('titulo') || '').trim();
      if (!titulo || titulo.length > 100) return reply(res, 400, {erro: 'Informe um título de 1 a 100 caracteres'});
      const [result] = await db.execute('INSERT INTO jogos (titulo) VALUES (?)', [titulo]);
      return reply(res, 201, {id: result.insertId, titulo});
    }
    if (url.pathname === '/jogos' && req.method === 'GET') {
      const [jogos] = await db.query('SELECT id, titulo FROM jogos ORDER BY id');
      return reply(res, 200, {jogos, consultas: await redis.incr('consultas')});
    }
    return reply(res, 404, {erro: 'Rota desconhecida'});
  } catch (err) {
    console.error(err.message);
    return reply(res, 503, {erro: 'Serviço temporariamente indisponível'});
  }
}).listen(3000, '0.0.0.0');
