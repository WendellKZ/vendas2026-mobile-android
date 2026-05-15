package com.vendas2026.mobile.data

import com.vendas2026.mobile.model.ApiResult
import com.vendas2026.mobile.model.PedidoResumo
import com.vendas2026.mobile.model.PedidoEnvio
import com.vendas2026.mobile.model.ClienteResumo
import com.vendas2026.mobile.model.CondicaoPagamentoResumo
import com.vendas2026.mobile.model.ProdutoResumo
import com.vendas2026.mobile.model.EmpresaResumo
import com.vendas2026.mobile.model.UsuarioLogado
import com.vendas2026.mobile.model.TransportadoraResumo
import com.vendas2026.mobile.model.MobileRemoteConfig
import org.json.JSONArray
import org.json.JSONObject
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

object ApiClient {
    private fun request(method: String, endpoint: String, token: String? = null, body: JSONObject? = null): String {
        val url = URL(AppConfig.API_BASE_URL.trimEnd('/') + endpoint)
        val conn = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = method
            connectTimeout = 12000
            readTimeout = 12000
            setRequestProperty("Accept", "application/json")
            setRequestProperty("Content-Type", "application/json")
            token?.let { setRequestProperty("Authorization", "Bearer $it") }
            if (body != null) doOutput = true
        }
        if (body != null) {
            OutputStreamWriter(conn.outputStream).use { it.write(body.toString()) }
        }
        val stream = if (conn.responseCode in 200..299) conn.inputStream else conn.errorStream
        val text = stream.bufferedReader().use { it.readText() }
        if (conn.responseCode !in 200..299) throw RuntimeException(text.ifBlank { "Erro HTTP ${conn.responseCode}" })
        return text
    }

    fun login(usuario: String, senha: String): ApiResult<UsuarioLogado> {
        return try {
            val body = JSONObject().put("usuario", usuario).put("email", usuario).put("senha", senha)
            val json = JSONObject(request("POST", AppConfig.ENDPOINT_LOGIN, body = body))
            val data = json.optJSONObject("usuario") ?: json
            ApiResult(
                ok = true,
                data = UsuarioLogado(
                    nome = data.optString("nome", usuario),
                    email = data.optString("email", usuario),
                    token = json.optString("token", data.optString("token", ""))
                )
            )
        } catch (e: Exception) {
            ApiResult(false, message = e.message ?: "Falha no login")
        }
    }

    fun empresas(token: String): ApiResult<List<EmpresaResumo>> {
        return try {
            val arr = JSONArray(request("GET", "/api/mobile/empresas", token = token))
            val list = mutableListOf<EmpresaResumo>()
            for (i in 0 until arr.length()) {
                val o = arr.getJSONObject(i)
                list.add(EmpresaResumo(
                    codigo = o.optString("codigo", o.optString("id", "")),
                    nome = o.optString("nome", o.optString("razao_social", "Empresa")),
                    documento = o.optString("cnpj", o.optString("documento", "")),
                    cidade = o.optString("cidade", ""),
                    destaque = o.optString("destaque", o.optString("segmento", ""))
                ))
            }
            ApiResult(true, list)
        } catch (e: Exception) {
            ApiResult(false, message = e.message ?: "Falha ao buscar empresas")
        }
    }

    fun produtos(token: String, empresaId: String): ApiResult<List<ProdutoResumo>> {
        return try {
            val arr = JSONArray(request("GET", AppConfig.ENDPOINT_PRODUTOS + "?empresa_id=" + empresaId, token = token))
            val list = mutableListOf<ProdutoResumo>()
            for (i in 0 until arr.length()) {
                val o = arr.getJSONObject(i)
                list.add(
                    ProdutoResumo(
                        codigo = o.optString("codigo", o.optString("id", "")),
                        nome = o.optString("nome", "Produto"),
                        estoque = o.optInt("estoque", 0),
                        preco = o.optString("preco_formatado", o.optString("preco", "R$ 0,00")),
                        categoria = o.optString("categoria", "Geral"),
                        descricao = o.optString("descricao", o.optString("descrição", "Produto cadastrado no ERP.")),
                        fotoRes = o.optString("foto_res", "produto_padrao"),
                        empresaId = o.optString("empresa_id", empresaId)
                    )
                )
            }
            ApiResult(true, list)
        } catch (e: Exception) {
            ApiResult(false, message = e.message ?: "Falha ao buscar produtos")
        }
    }

    fun pedidos(token: String, empresaId: String): ApiResult<List<PedidoResumo>> {
        return try {
            val arr = JSONArray(request("GET", AppConfig.ENDPOINT_PEDIDOS + "?empresa_id=" + empresaId, token = token))
            val list = mutableListOf<PedidoResumo>()
            for (i in 0 until arr.length()) {
                val o = arr.getJSONObject(i)
                val status = o.optString("status", "Orçamento")
                list.add(
                    PedidoResumo(
                        numero = o.optString("numero", o.optString("id", "")),
                        cliente = o.optString("cliente", "Cliente"),
                        total = o.optString("total_formatado", o.optString("total", "R$ 0,00")),
                        status = status,
                        podeEditar = o.optBoolean("pode_editar", !status.equals("Integrado", ignoreCase = true)),
                        empresaId = o.optString("empresa_id", empresaId)
                    )
                )
            }
            ApiResult(true, list)
        } catch (e: Exception) {
            ApiResult(false, message = e.message ?: "Falha ao buscar pedidos")
        }
    }
    fun clientes(token: String): ApiResult<List<ClienteResumo>> {
        return try {
            val arr = JSONArray(request("GET", AppConfig.ENDPOINT_CLIENTES, token = token))
            val list = mutableListOf<ClienteResumo>()
            for (i in 0 until arr.length()) {
                val o = arr.getJSONObject(i)
                list.add(
                    ClienteResumo(
                        codigo = o.optString("codigo", o.optString("id", "")),
                        nome = o.optString("nome", "Cliente"),
                        cidade = o.optString("cidade", "")
                    )
                )
            }
            ApiResult(true, list)
        } catch (e: Exception) {
            ApiResult(false, message = e.message ?: "Falha ao buscar clientes")
        }
    }


    fun transportadoras(token: String): ApiResult<List<TransportadoraResumo>> {
        return try {
            val arr = JSONArray(request("GET", AppConfig.ENDPOINT_TRANSPORTADORAS, token = token))
            val list = mutableListOf<TransportadoraResumo>()
            for (i in 0 until arr.length()) {
                val o = arr.getJSONObject(i)
                list.add(
                    TransportadoraResumo(
                        codigo = o.optString("codigo", o.optString("id", "")),
                        nome = o.optString("nome", "Transportadora"),
                        prazo = o.optString("prazo", o.optString("prazo_entrega", "")),
                        frete = o.optString("frete", o.optString("frete_formatado", "A calcular"))
                    )
                )
            }
            ApiResult(true, list)
        } catch (e: Exception) {
            ApiResult(false, message = e.message ?: "Falha ao buscar transportadoras")
        }
    }


    fun condicoesPagamento(token: String): ApiResult<List<CondicaoPagamentoResumo>> {
        return try {
            val arr = JSONArray(request("GET", AppConfig.ENDPOINT_CONDICOES_PAGAMENTO, token = token))
            val list = mutableListOf<CondicaoPagamentoResumo>()
            for (i in 0 until arr.length()) {
                val o = arr.getJSONObject(i)
                list.add(
                    CondicaoPagamentoResumo(
                        codigo = o.optString("codigo", o.optString("id", "")),
                        descricao = o.optString("descricao", o.optString("nome", "Condição de pagamento")),
                        prazo = o.optString("prazo", o.optString("parcelas", ""))
                    )
                )
            }
            ApiResult(true, list)
        } catch (e: Exception) {
            ApiResult(false, message = e.message ?: "Falha ao buscar condições de pagamento")
        }
    }


    fun mobileConfig(token: String): ApiResult<MobileRemoteConfig> {
        return try {
            val o = JSONObject(request("GET", AppConfig.ENDPOINT_CONFIG_MOBILE, token = token))
            val cfg = o.optJSONObject("config") ?: o
            ApiResult(true, MobileRemoteConfig(
                appVersionLabel = cfg.optString("app_version_label", cfg.optString("versao", "V38")),
                mensagemHome = cfg.optString("mensagem_home", ""),
                corPrimaria = cfg.optString("cor_primaria", "#2563EB"),
                mostrarNotificacoes = cfg.optBoolean("mostrar_notificacoes", true),
                mostrarRota = cfg.optBoolean("mostrar_rota", true),
                mostrarHistorico = cfg.optBoolean("mostrar_historico", true),
                mostrarCampanhas = cfg.optBoolean("mostrar_campanhas", true),
                mostrarOffline = cfg.optBoolean("mostrar_offline", true),
                mostrarEmpresa = cfg.optBoolean("mostrar_empresa", true),
                labelNovoPedido = cfg.optString("label_novo_pedido", "Novo pedido"),
                labelPedidos = cfg.optString("label_pedidos", "Pedidos"),
                labelProdutos = cfg.optString("label_produtos", "Produtos"),
                labelClientes = cfg.optString("label_clientes", "Clientes"),
                labelNovoCliente = cfg.optString("label_novo_cliente", "Novo cliente"),
                labelTransportadora = cfg.optString("label_transportadora", "Transportadora")
            ))
        } catch (e: Exception) {
            ApiResult(false, message = e.message ?: "Configuração remota indisponível")
        }
    }

    fun criarPedido(token: String, pedido: PedidoEnvio): ApiResult<PedidoResumo> {
        return try {
            val itens = JSONArray()
            pedido.itens.forEach { item ->
                itens.put(JSONObject()
                    .put("codigo_produto", item.codigoProduto)
                    .put("nome_produto", item.nomeProduto)
                    .put("quantidade", item.quantidade)
                    .put("preco_unitario", item.precoUnitario)
                    .put("desconto_percentual", item.descontoPercentual)
                    .put("subtotal_com_desconto", item.subtotalComDesconto)
                )
            }
            val body = JSONObject()
                .put("empresa_id", pedido.empresaId)
                .put("empresa_nome", pedido.empresaNome)
                .put("codigo_cliente", pedido.codigoCliente)
                .put("nome_cliente", pedido.nomeCliente)
                .put("codigo_transportadora", pedido.codigoTransportadora)
                .put("nome_transportadora", pedido.nomeTransportadora)
                .put("codigo_condicao_pagamento", pedido.codigoCondicaoPagamento)
                .put("condicao_pagamento", pedido.condicaoPagamento)
                .put("observacao", pedido.observacao)
                .put("total", pedido.total)
                .put("origem", pedido.origem)
                .put("tipo_finalizacao", pedido.tipoFinalizacao)
                .put("acao", pedido.tipoFinalizacao)
                .put("status_solicitado", if (pedido.tipoFinalizacao == "APROVACAO") "EM_APROVACAO" else "ORCAMENTO")
                .put("manter_orcamento", pedido.tipoFinalizacao == "ORCAMENTO")
                .put("itens", itens)
            val o = JSONObject(request("POST", AppConfig.ENDPOINT_CRIAR_PEDIDO, token = token, body = body))
            val status = o.optString("status", "Orçamento")
            ApiResult(true, PedidoResumo(
                numero = o.optString("numero", o.optString("id", "APP")),
                cliente = o.optString("cliente", pedido.nomeCliente),
                total = o.optString("total_formatado", o.optString("total", pedido.total)),
                status = status,
                podeEditar = o.optBoolean("pode_editar", true),
                empresaId = o.optString("empresa_id", pedido.empresaId)
            ))
        } catch (e: Exception) {
            ApiResult(false, message = e.message ?: "Falha ao criar pedido")
        }
    }

}
