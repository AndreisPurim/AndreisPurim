module.exports = {
  entry : "./src/entry",
    resolve: {
        fallback: { 
            path: require.resolve("path-browserify") }
    },
}