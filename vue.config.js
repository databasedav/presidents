module.exports = {
  devServer: {
    proxy: {
      '/socket.io': {
        target: 'http://localhost:5000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
  outputDir: './src/server/app/static',
  chainWebpack: config => {
    config
      .entry('app')
        .clear()
        .add('./src/client/main.js')
        .end()
  }
};