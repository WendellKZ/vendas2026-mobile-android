package com.vendas2026.mobile.data

import com.vendas2026.mobile.model.ApiResult
import com.vendas2026.mobile.model.ClienteResumo
import com.vendas2026.mobile.model.CondicaoPagamentoResumo
import com.vendas2026.mobile.model.PedidoResumo
import com.vendas2026.mobile.model.EmpresaResumo
import com.vendas2026.mobile.model.PedidoEnvio
import com.vendas2026.mobile.model.ProdutoResumo
import com.vendas2026.mobile.model.UsuarioLogado
import com.vendas2026.mobile.model.TransportadoraResumo
import com.vendas2026.mobile.model.MobileRemoteConfig

object MobileRepository {
    fun login(usuario: String, senha: String): ApiResult<UsuarioLogado> {
        if (AppConfig.MOCK_MODE) return ApiResult(true, MockRepository.login(usuario, senha))
        return ApiClient.login(usuario, senha)
    }

    fun empresas(token: String): ApiResult<List<EmpresaResumo>> {
        if (AppConfig.MOCK_MODE) return ApiResult(true, MockRepository.empresas)
        return ApiClient.empresas(token)
    }

    fun produtos(token: String, empresaId: String): ApiResult<List<ProdutoResumo>> {
        if (AppConfig.MOCK_MODE) return ApiResult(true, MockRepository.produtos(empresaId))
        return ApiClient.produtos(token, empresaId)
    }

    fun pedidos(token: String, empresaId: String): ApiResult<List<PedidoResumo>> {
        if (AppConfig.MOCK_MODE) return ApiResult(true, MockRepository.pedidos(empresaId))
        return ApiClient.pedidos(token, empresaId)
    }

    fun clientes(token: String): ApiResult<List<ClienteResumo>> {
        if (AppConfig.MOCK_MODE) return ApiResult(true, MockRepository.clientes)
        return ApiClient.clientes(token)
    }

    fun transportadoras(token: String): ApiResult<List<TransportadoraResumo>> {
        if (AppConfig.MOCK_MODE) return ApiResult(true, MockRepository.transportadoras)
        return ApiClient.transportadoras(token)
    }

    fun condicoesPagamento(token: String): ApiResult<List<CondicaoPagamentoResumo>> {
        if (AppConfig.MOCK_MODE) return ApiResult(true, MockRepository.condicoesPagamento)
        return ApiClient.condicoesPagamento(token)
    }


    fun mobileConfig(token: String): ApiResult<MobileRemoteConfig> {
        if (AppConfig.MOCK_MODE) return ApiResult(true, MobileRemoteConfig())
        return ApiClient.mobileConfig(token)
    }

    fun criarPedido(token: String, pedido: PedidoEnvio): ApiResult<PedidoResumo> {
        if (AppConfig.MOCK_MODE) {
            val numero = "APP-${System.currentTimeMillis().toString().takeLast(5)}"
            return ApiResult(true, PedidoResumo(numero, pedido.nomeCliente, pedido.total, "Orçamento", true, pedido.empresaId))
        }
        return ApiClient.criarPedido(token, pedido)
    }
}
