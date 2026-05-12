package com.vendas2026.mobile.model

data class UsuarioLogado(
    val nome: String,
    val email: String,
    val token: String
)

data class EmpresaResumo(
    val codigo: String,
    val nome: String,
    val documento: String = "",
    val cidade: String = "",
    val destaque: String = ""
)

data class PedidoResumo(
    val numero: String,
    val cliente: String,
    val total: String,
    val status: String,
    val podeEditar: Boolean,
    val empresaId: String = "1"
)

data class ProdutoResumo(
    val codigo: String,
    val nome: String,
    val estoque: Int,
    val preco: String,
    val categoria: String = "Geral",
    val descricao: String = "Produto cadastrado para venda no app.",
    val fotoRes: String = "produto_padrao",
    val empresaId: String = "1"
)

data class ClienteResumo(
    val codigo: String,
    val nome: String,
    val cidade: String
)

data class TransportadoraResumo(
    val codigo: String,
    val nome: String,
    val prazo: String,
    val frete: String
)

data class CondicaoPagamentoResumo(
    val codigo: String,
    val descricao: String,
    val prazo: String
)

data class CarrinhoItem(
    val produto: ProdutoResumo,
    var quantidade: Int,
    var descontoPercentual: Double = 0.0
)

data class PedidoEnvioItem(
    val codigoProduto: String,
    val nomeProduto: String,
    val quantidade: Int,
    val precoUnitario: String,
    val descontoPercentual: Double = 0.0,
    val subtotalComDesconto: String = "R$ 0,00"
)

data class PedidoEnvio(
    val empresaId: String,
    val empresaNome: String,
    val codigoCliente: String,
    val nomeCliente: String,
    val codigoTransportadora: String,
    val nomeTransportadora: String,
    val codigoCondicaoPagamento: String,
    val condicaoPagamento: String,
    val observacao: String,
    val itens: List<PedidoEnvioItem>,
    val total: String,
    val origem: String = "APP_ANDROID"
)

data class ApiResult<T>(
    val ok: Boolean,
    val data: T? = null,
    val message: String = ""
)
