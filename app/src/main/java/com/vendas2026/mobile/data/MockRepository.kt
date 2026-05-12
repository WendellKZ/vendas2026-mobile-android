package com.vendas2026.mobile.data

import com.vendas2026.mobile.model.ClienteResumo
import com.vendas2026.mobile.model.CondicaoPagamentoResumo
import com.vendas2026.mobile.model.EmpresaResumo
import com.vendas2026.mobile.model.PedidoResumo
import com.vendas2026.mobile.model.ProdutoResumo
import com.vendas2026.mobile.model.TransportadoraResumo
import com.vendas2026.mobile.model.UsuarioLogado

object MockRepository {
    fun login(usuario: String, senha: String): UsuarioLogado {
        val nome = when {
            usuario.contains("admin", ignoreCase = true) -> "Administrador"
            usuario.contains("vendedor", ignoreCase = true) -> "Vendedor Demo"
            usuario.isNotBlank() -> usuario
            else -> "Usuário Demo"
        }
        return UsuarioLogado(nome = nome, email = usuario.ifBlank { "vendedor@demo.com" }, token = "mock-token-v3")
    }

    val empresas = listOf(
        EmpresaResumo("1", "Líder Brinquedos", "00.000.000/0001-00", "São Bernardo/SP", "Catálogo principal"),
        EmpresaResumo("2", "Líder Baby", "00.000.000/0002-00", "São Paulo/SP", "Linha bebê"),
        EmpresaResumo("3", "Líder Distribuição", "00.000.000/0003-00", "Campinas/SP", "Atacado e distribuição")
    )

    fun pedidos(empresaId: String) = pedidosBase.filter { it.empresaId == empresaId }
    fun produtos(empresaId: String) = produtosBase.filter { it.empresaId == empresaId }

    private val pedidosBase = listOf(
        PedidoResumo("000128", "Mercado Nova Era", "R$ 2.480,90", "Orçamento", true, "1"),
        PedidoResumo("000129", "Distribuidora Alfa", "R$ 7.320,00", "Aprovado", true, "1"),
        PedidoResumo("000130", "Loja Infantil Sol", "R$ 1.945,50", "Integrado", false, "2"),
        PedidoResumo("000131", "Brinquedos Central", "R$ 4.210,70", "Em digitação", true, "3")
    )

    val clientes = listOf(
        ClienteResumo("C001", "Mercado Nova Era", "Santo André/SP"),
        ClienteResumo("C002", "Distribuidora Alfa", "São Bernardo/SP"),
        ClienteResumo("C003", "Loja Infantil Sol", "São Paulo/SP"),
        ClienteResumo("C004", "Brinquedos Central", "Campinas/SP"),
        ClienteResumo("C005", "Atacado Kids Brasil", "Guarulhos/SP")
    )

    val transportadoras = listOf(
        TransportadoraResumo("T001", "Retira / Sem transportadora", "Cliente retira", "R$ 0,00"),
        TransportadoraResumo("T002", "Rodonaves", "3 a 5 dias", "A combinar"),
        TransportadoraResumo("T003", "Jadlog", "2 a 4 dias", "A calcular"),
        TransportadoraResumo("T004", "Braspress", "4 a 7 dias", "A calcular"),
        TransportadoraResumo("T005", "Transportadora do Cliente", "Conforme cliente", "Por conta cliente")
    )

    val condicoesPagamento = listOf(
        CondicaoPagamentoResumo("001", "À vista", "0 dia"),
        CondicaoPagamentoResumo("007", "7 dias", "7 dias"),
        CondicaoPagamentoResumo("014", "14 dias", "14 dias"),
        CondicaoPagamentoResumo("021", "21 dias", "21 dias"),
        CondicaoPagamentoResumo("030", "30 dias", "30 dias"),
        CondicaoPagamentoResumo("283", "28/35/42 dias", "parcelado")
    )

    private val produtosBase = listOf(
        ProdutoResumo("1001", "Carrinho Infantil Premium", 42, "R$ 89,90", "Brinquedos", "Carrinho infantil com acabamento premium, ideal para venda em lojas de brinquedos e presentes.", "produto_carrinho", "1"),
        ProdutoResumo("1002", "Boneca Coleção Especial", 18, "R$ 129,90", "Bonecas", "Boneca de coleção especial com embalagem reforçada e alto apelo de vitrine.", "produto_boneca", "1"),
        ProdutoResumo("2001", "Kit Bebê Educativo", 16, "R$ 59,90", "Bebê", "Kit educativo para bebês. Produto aparece na empresa Líder Baby.", "produto_bebe", "2"),
        ProdutoResumo("2002", "Mordedor Silicone Bebê", 75, "R$ 24,90", "Bebê", "Mordedor de silicone macio, fácil de vender em recompra e mix de bebê.", "produto_mordedor", "2"),
        ProdutoResumo("3001", "Jogo Educativo Cores", 31, "R$ 44,90", "Educativo", "Jogo educativo para aprendizagem de cores, indicado para venda consultiva.", "produto_educativo", "3"),
        ProdutoResumo("3002", "Tapete Atividades Bebê", 22, "R$ 149,90", "Bebê", "Tapete de atividades com maior ticket médio e boa composição para pedidos de linha bebê.", "produto_tapete", "3")
    )
}
