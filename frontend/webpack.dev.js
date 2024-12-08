const { merge } = require("webpack-merge");
const common = require("./webpack.common.js");

module.exports = merge(common, {
    mode: "development",
    devServer: {
        compress: true,
        port: 3000,
        proxy: [
            {
                context: ["/data", "/processing"],
                target: "http://localhost:8000",
            },
        ],
    },
    devtool: "inline-source-map", // Для более легкой отладки
});
