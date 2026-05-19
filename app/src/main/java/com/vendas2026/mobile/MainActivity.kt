package com.vendas2026.mobile

import android.app.Activity
import android.content.Intent
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.Path
import android.graphics.pdf.PdfDocument
import android.net.Uri
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.view.Window
import android.text.Editable
import android.text.InputType
import android.text.TextWatcher
import android.view.Gravity
import android.view.View
import android.widget.*
import com.vendas2026.mobile.data.AppConfig
import com.vendas2026.mobile.data.MobileRepository
import com.vendas2026.mobile.data.MockRepository
import com.vendas2026.mobile.model.ApiResult
import com.vendas2026.mobile.model.CarrinhoItem
import com.vendas2026.mobile.model.ClienteResumo
import com.vendas2026.mobile.model.CondicaoPagamentoResumo
import com.vendas2026.mobile.model.PedidoResumo
import com.vendas2026.mobile.model.EmpresaResumo
import com.vendas2026.mobile.model.PedidoEnvio
import com.vendas2026.mobile.model.PedidoEnvioItem
import com.vendas2026.mobile.model.ProdutoResumo
import com.vendas2026.mobile.model.UsuarioLogado
import com.vendas2026.mobile.model.TransportadoraResumo
import com.vendas2026.mobile.model.MobileRemoteConfig
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.io.File
import java.text.NumberFormat
import java.util.Locale

class MainActivity : Activity() {
    private lateinit var root: LinearLayout
    private var usuarioLogado: UsuarioLogado? = null
    private var empresaAtiva: EmpresaResumo? = null
    private var empresasCache: List<EmpresaResumo> = emptyList()
    private var produtosCache: List<ProdutoResumo> = emptyList()
    private var clientesCache: List<ClienteResumo> = emptyList()
    private var clienteSelecionado: ClienteResumo? = null
    private var transportadorasCache: List<TransportadoraResumo> = emptyList()
    private var transportadoraSelecionada: TransportadoraResumo? = null
    private var condicoesPagamentoCache: List<CondicaoPagamentoResumo> = emptyList()
    private var condicaoPagamentoSelecionada: CondicaoPagamentoResumo? = null
    private var observacaoPedido: String = ""
    private val carrinho = mutableListOf<CarrinhoItem>()
    private val pedidosCriados = mutableListOf<PedidoResumo>()
    private val clientesCriados = mutableListOf<ClienteResumo>()
    private val transportadorasCriadas = mutableListOf<TransportadoraResumo>()
    private val pedidosPendentesSync = mutableListOf<PedidoEnvio>()
    private var assinaturaClienteRegistrada: Boolean = false
    private var ultimaSincronizacaoInfo: String = "Toque em sincronizar para enviar pendências e receber atualizações do ERP."
    private var remoteConfig: MobileRemoteConfig = MobileRemoteConfig()

    // Paleta alinhada ao ERP Web Vendas 2026 / PedidoGo
    private val azul = Color.rgb(37, 99, 235)          // #2563EB
    private val azulClaro = Color.rgb(40, 100, 135)    // #286487
    private val azulProfundo = Color.rgb(23, 56, 92)   // #17385C
    private val azulEscuro = Color.rgb(15, 23, 42)     // #0F172A
    private val cinzaTexto = Color.rgb(100, 116, 139)  // #64748B
    private val fundo = Color.rgb(245, 248, 252)       // #F5F8FC
    private val verde = Color.rgb(5, 150, 105)         // #059669
    private val vermelho = Color.rgb(220, 38, 38)      // #DC2626
    private val amarelo = Color.rgb(217, 119, 6)       // #D97706
    private val azulBotao = Color.rgb(21, 94, 239)     // #155EEF
    private val azulBotaoEscuro = Color.rgb(0, 53, 158)// #00359E
    private val bordaWeb = Color.rgb(219, 228, 239)    // #DBE4EF
    private val azulSoft = Color.rgb(238, 246, 255)    // #EEF6FF
    private val inputSoft = Color.rgb(248, 251, 255)   // #F8FBFF

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = fundo
        window.navigationBarColor = fundo
        loadSavedApiConfig()
        showLogin()
    }

    private fun loadSavedApiConfig() {
        val prefs = getSharedPreferences("vendas2026_config", MODE_PRIVATE)
        val savedUrl = prefs.getString("api_base_url", null)
        if (!savedUrl.isNullOrBlank()) {
            AppConfig.API_BASE_URL = normalizeApiUrl(savedUrl)
        }
    }

    private fun saveApiConfig(url: String) {
        val normalized = normalizeApiUrl(url)
        AppConfig.API_BASE_URL = normalized
        getSharedPreferences("vendas2026_config", MODE_PRIVATE)
            .edit()
            .putString("api_base_url", normalized)
            .apply()
    }

    private fun normalizeApiUrl(url: String): String {
        var value = url.trim()
        if (value.isBlank()) return AppConfig.DEFAULT_API_BASE_URL
        if (!value.startsWith("http://") && !value.startsWith("https://")) value = "http://$value"
        return value.trimEnd('/')
    }

    private fun setScreen(content: LinearLayout) {
        val scroll = ScrollView(this)
        scroll.setBackgroundColor(fundo)
        scroll.addView(content)
        setContentView(scroll)
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    private fun baseRoot(): LinearLayout = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        setBackgroundColor(fundo)
        // Safe area reforçada: desce o conteúdo para não encostar na hora, bateria, Wi-Fi ou câmera do aparelho.
        setPadding(dp(20), dp(58), dp(20), dp(30))
    }

    private fun title(text: String): TextView = TextView(this).apply {
        this.text = text
        textSize = 25f
        setTextColor(azulEscuro)
        typeface = Typeface.create("sans-serif-medium", Typeface.BOLD)
        setPadding(0, 10, 0, 8)
    }

    private fun subtitle(text: String): TextView = TextView(this).apply {
        this.text = text
        textSize = 14f
        setTextColor(cinzaTexto)
        setPadding(0, 0, 0, 18)
    }

    private fun sectionLabel(text: String): TextView = TextView(this).apply {
        this.text = text.uppercase()
        textSize = 12f
        typeface = Typeface.DEFAULT_BOLD
        setTextColor(azul)
        setPadding(0, 18, 0, 8)
    }

    private fun pedidoHeader(etapa: Int, titulo: String, descricao: String): View {
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.WHITE)
            setPadding(26, 22, 26, 22)
            layoutParams = LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, 0, 0, 18) }
        }
        box.addView(TextView(this).apply {
            text = "Pedido"
            textSize = 24f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(azulEscuro)
        })
        box.addView(TextView(this).apply {
            text = titulo
            textSize = 16f
            typeface = Typeface.create("sans-serif-medium", Typeface.BOLD)
            setTextColor(azul)
            setPadding(0, 6, 0, 6)
        })
        box.addView(progressEtapas(etapa))
        return box
    }

    private fun progressEtapas(etapaAtual: Int): View {
        val row = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        val etapas = listOf("Cliente", "Transp.", "Pagto", "Itens", "Fechar")
        etapas.forEachIndexed { index, label ->
            val active = index + 1 <= etapaAtual
            row.addView(TextView(this).apply {
                text = "${index + 1}. $label"
                textSize = 12f
                gravity = Gravity.CENTER
                typeface = Typeface.DEFAULT_BOLD
                setTextColor(if (active) Color.WHITE else cinzaTexto)
                setBackgroundColor(if (active) azul else bordaWeb)
                setPadding(8, 10, 8, 10)
            }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(3, 0, 3, 0) })
        }
        return row
    }

    private fun resumoPedidoCard(acaoCarrinho: Boolean = true): View {
        val cliente = clienteSelecionado?.nome ?: "Selecione um cliente"
        val transp = transportadoraSelecionada?.nome ?: "Selecione a transportadora"
        val itens = carrinho.sumOf { it.quantidade }
        val total = formatCurrency(totalCarrinho())
        val desc = "Cliente: $cliente\nTransportadora: $transp\nItens: $itens • Total: $total"
        return if (acaoCarrinho) card("Resumo do pedido", desc, "Abrir carrinho") { showCarrinho() } else card("Resumo do pedido", desc, "Continuar") { }
    }

    private fun button(text: String, onClick: () -> Unit): Button = Button(this).apply {
        this.text = text.uppercase()
        textSize = 12.5f
        setTextColor(Color.WHITE)
        background = gradientBg(azulBotao, azulBotaoEscuro, 34f)
        typeface = Typeface.create("sans-serif-medium", Typeface.BOLD)
        minHeight = 56
        setPadding(20, 10, 20, 10)
        setOnClickListener { onClick() }
    }

    private fun secondaryButton(text: String, onClick: () -> Unit): Button = Button(this).apply {
        this.text = text.uppercase()
        textSize = 12f
        setTextColor(azulEscuro)
        background = roundedBg(Color.WHITE, 32f, bordaWeb)
        typeface = Typeface.create("sans-serif-medium", Typeface.BOLD)
        minHeight = 52
        setPadding(18, 8, 18, 8)
        setOnClickListener { onClick() }
    }


    private fun successButton(text: String, onClick: () -> Unit): Button = Button(this).apply {
        this.text = text.uppercase()
        textSize = 12.5f
        setTextColor(Color.WHITE)
        background = gradientBg(Color.rgb(22, 101, 52), Color.rgb(34, 197, 94), 34f)
        typeface = Typeface.create("sans-serif-medium", Typeface.BOLD)
        minHeight = 54
        setPadding(18, 8, 18, 8)
        setOnClickListener { onClick() }
    }

    private fun budgetButton(text: String, onClick: () -> Unit): Button = Button(this).apply {
        this.text = text.uppercase()
        textSize = 12.5f
        setTextColor(Color.WHITE)
        background = gradientBg(Color.rgb(217, 119, 6), Color.rgb(245, 158, 11), 34f)
        typeface = Typeface.create("sans-serif-medium", Typeface.BOLD)
        minHeight = 54
        setPadding(18, 8, 18, 8)
        setOnClickListener { onClick() }
    }

    private fun topBackBar(titulo: String = "", onBack: () -> Unit): View {
        val row = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, 0, 0, 16)
        }
        row.addView(TextView(this).apply {
            text = "‹"
            textSize = 42f
            typeface = Typeface.DEFAULT_BOLD
            gravity = Gravity.CENTER
            setTextColor(azulEscuro)
            setPadding(4, 0, 18, 0)
            setOnClickListener { onBack() }
        }, LinearLayout.LayoutParams(-2, dp(52)))
        row.addView(TextView(this).apply {
            text = titulo
            textSize = 19f
            typeface = Typeface.create("sans-serif-medium", Typeface.BOLD)
            setTextColor(azulEscuro)
            gravity = Gravity.CENTER_VERTICAL
        }, LinearLayout.LayoutParams(0, -2, 1f))
        return row
    }


    private fun infoBox(texto: String): View = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        background = roundedBg(azulSoft, 26f, Color.rgb(191, 219, 254))
        setPadding(22, 18, 22, 18)
        layoutParams = LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, 8, 0, 18) }
        addView(TextView(context).apply {
            text = texto
            textSize = 14f
            setTextColor(azulEscuro)
            setLineSpacing(4f, 1.0f)
        })
    }

    private fun formSection(titulo: String, icone: String, vararg campos: View): View {
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            background = roundedBg(Color.WHITE, 32f, bordaWeb)
            setPadding(22, 18, 22, 18)
            layoutParams = LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, 0, 0, 18) }
        }
        box.addView(TextView(this).apply {
            text = "$icone  $titulo"
            textSize = 18f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(azulEscuro)
            setPadding(0, 0, 0, 12)
        })
        campos.forEach { box.addView(it) }
        return box
    }

    private fun premiumInput(label: String, hintText: String, inputTypeValue: Int = InputType.TYPE_CLASS_TEXT, enabled: Boolean = true, minLinesValue: Int = 1): EditText {
        return EditText(this).apply {
            hint = hintText
            textSize = 15f
            inputType = inputTypeValue
            isEnabled = enabled
            if (minLinesValue <= 1) setSingleLine(true) else { setSingleLine(false); minLines = minLinesValue }
            setPadding(18, 12, 18, 12)
            background = roundedBg(inputSoft, 22f, Color.rgb(203, 213, 225))
            layoutParams = LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, 0, 0, 14) }
        }
    }

    private fun labeledField(label: String, field: EditText): View {
        val box = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        box.addView(TextView(this).apply {
            text = label
            textSize = 12f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(azulEscuro)
            setPadding(2, 0, 0, 6)
        })
        box.addView(field)
        return box
    }

    private fun twoColumns(left: View, right: View): View = LinearLayout(this).apply {
        orientation = LinearLayout.HORIZONTAL
        addView(left, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(0, 0, 8, 0) })
        addView(right, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(8, 0, 0, 0) })
    }


    private fun premiumSearchBox(hintText: String, onBuscar: (String) -> Unit, onLimpar: () -> Unit): View {
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            background = roundedBg(Color.WHITE, 32f, bordaWeb)
            setPadding(22, 18, 22, 18)
            layoutParams = LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, 0, 0, 18) }
        }
        box.addView(TextView(this).apply {
            text = "🔎  Busca rápida"
            textSize = 18f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(azulEscuro)
            setPadding(0, 0, 0, 12)
        })
        val busca = premiumInput("Busca", hintText)
        box.addView(busca)
        val rowBusca = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        rowBusca.addView(button("Buscar") { onBuscar(busca.text.toString().trim()) }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(0,0,8,0) })
        rowBusca.addView(secondaryButton("Limpar") { onLimpar() }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(8,0,0,0) })
        box.addView(rowBusca)
        return box
    }

    private fun statusBadge(texto: String, cor: Int): TextView = TextView(this).apply {
        text = texto.uppercase()
        textSize = 12f
        typeface = Typeface.DEFAULT_BOLD
        setTextColor(Color.WHITE)
        gravity = Gravity.CENTER
        background = roundedBg(cor, 20f)
        setPadding(14, 8, 14, 8)
    }

    private fun miniInfo(label: String, valor: String, destaque: Boolean = false): View = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        background = roundedBg(inputSoft, 22f, bordaWeb)
        setPadding(16, 12, 16, 12)
        addView(TextView(context).apply { text = label.uppercase(); textSize = 10f; typeface = Typeface.DEFAULT_BOLD; setTextColor(cinzaTexto) })
        addView(TextView(context).apply { text = valor; textSize = if (destaque) 18f else 14f; typeface = Typeface.DEFAULT_BOLD; setTextColor(if (destaque) azul else azulEscuro) })
    }


    private fun servidorAtualCard(): View {
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            background = roundedBg(azulSoft, 28f, Color.rgb(191, 219, 254))
            setPadding(18, 14, 18, 14)
            layoutParams = LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, 0, 0, 16) }
        }
        val row = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        row.addView(TextView(this).apply {
            text = "🌐"
            textSize = 22f
            gravity = Gravity.CENTER
        }, LinearLayout.LayoutParams(dp(42), -2))
        row.addView(TextView(this).apply {
            text = "Servidor\n${AppConfig.API_BASE_URL}"
            textSize = 12.5f
            setTextColor(azulEscuro)
            typeface = Typeface.create("sans-serif-medium", Typeface.BOLD)
        }, LinearLayout.LayoutParams(0, -2, 1f))
        row.addView(TextView(this).apply {
            text = "Alterar"
            textSize = 13f
            setTextColor(azul)
            typeface = Typeface.DEFAULT_BOLD
            gravity = Gravity.CENTER
            setPadding(14, 10, 14, 10)
            setOnClickListener { showConfig() }
        })
        box.addView(row)
        return box
    }

    private fun showLogin() {
        root = baseRoot()
        root.gravity = Gravity.CENTER_HORIZONTAL
        setScreen(root)

        val hero = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            background = gradientBg(azulProfundo, azulClaro, 44f)
            setPadding(28, 28, 28, 28)
            layoutParams = LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, 0, 0, 22) }
        }
        hero.addView(TextView(this).apply {
            text = "VENDAS 2026"
            textSize = 11f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(Color.WHITE)
            background = roundedBg(Color.argb(70, 255, 255, 255), 24f, Color.argb(90, 255, 255, 255))
            setPadding(18, 8, 18, 8)
        })
        hero.addView(TextView(this).apply {
            text = "Vendas 2026"
            textSize = 31f
            typeface = Typeface.create("sans-serif-medium", Typeface.BOLD)
            setTextColor(Color.WHITE)
            setPadding(0, 18, 0, 8)
        })
        root.addView(hero)
        root.addView(servidorAtualCard())

        val cardLogin = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            background = roundedBg(Color.WHITE, 36f, bordaWeb)
            setPadding(24, 22, 24, 24)
        }
        cardLogin.addView(TextView(this).apply {
            text = "Entrar"
            textSize = 22f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(azulEscuro)
            setPadding(0, 0, 0, 4)
        })
        val usuario = premiumInput("Usuário", "Usuário / e-mail")
        val senha = premiumInput("Senha", "Senha", InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD)
        cardLogin.addView(labeledField("Usuário / e-mail", usuario))
        cardLogin.addView(labeledField("Senha", senha))
        cardLogin.addView(button("Entrar") {
            if (usuario.text.isBlank() || senha.text.isBlank()) Toast.makeText(this, "Informe usuário e senha", Toast.LENGTH_SHORT).show()
            else doLogin(usuario.text.toString(), senha.text.toString())
        })
        cardLogin.addView(secondaryButton("⚙ Alterar URL do ERP Render") { showConfig() }, LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, dp(10), 0, 0) })
        root.addView(cardLogin)
    }

    private fun doLogin(usuario: String, senha: String) {
        showLoading("Entrando no app...")
        Thread {
            val result = MobileRepository.login(usuario, senha)
            runOnUiThread {
                if (result.ok && result.data != null) { usuarioLogado = result.data; loadEmpresas() }
                else {
                    val msg = result.message.ifBlank { "Falha no login" }
                    Toast.makeText(this, "$msg. Confira o servidor/IP do ERP.", Toast.LENGTH_LONG).show()
                    showLogin()
                }
            }
        }.start()
    }

    private fun showLoading(msg: String) {
        root = baseRoot()
        root.gravity = Gravity.CENTER
        setScreen(root)
        root.addView(ProgressBar(this))
        root.addView(TextView(this).apply { text = msg; textSize = 16f; setTextColor(cinzaTexto); gravity = Gravity.CENTER; setPadding(0,16,0,0) })
    }

    private fun empresaIdAtiva(): String = empresaAtiva?.codigo ?: "1"

    private fun loadEmpresas() {
        showLoading("Carregando...")
        Thread {
            val result = MobileRepository.empresas(usuarioLogado?.token ?: "")
            runOnUiThread {
                if (result.ok && result.data != null) {
                    empresasCache = result.data
                    if (empresasCache.size == 1) { empresaAtiva = empresasCache.first(); showHome() }
                    else showSelecionarEmpresa(empresasCache)
                } else {
                    Toast.makeText(this, result.message.ifBlank { "Falha ao carregar empresas" }, Toast.LENGTH_LONG).show()
                    showLogin()
                }
            }
        }.start()
    }

    private fun showSelecionarEmpresa(empresas: List<EmpresaResumo>) {
        root = baseRoot()
        setScreen(root)
        root.addView(TextView(this).apply {
            text = "Escolha a empresa"
            textSize = 28f
            typeface = Typeface.create("sans-serif-medium", Typeface.BOLD)
            setTextColor(azulEscuro)
            setPadding(0, 0, 0, 8)
        })
        root.addView(subtitle("Selecione a empresa"))
        empresas.forEach { emp ->
            val desc = listOf(emp.documento, emp.cidade, emp.destaque).filter { it.isNotBlank() }.joinToString(" • ")
            root.addView(card("🏢 ${emp.nome}", desc.ifBlank { "Selecionar" }, "Entrar") {
                empresaAtiva = emp
                produtosCache = emptyList()
                clientesCache = emptyList()
                carrinho.clear()
                showHome()
            })
        }
        root.addView(secondaryButton("Voltar ao login") { usuarioLogado = null; empresaAtiva = null; showLogin() }, LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, 18, 0, 0) })
    }


    private fun homeHero(nome: String): View {
        val hero = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            background = gradientBg(azulProfundo, azulClaro, 42f)
            setPadding(26, 24, 26, 24)
            layoutParams = LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, 0, 0, 18) }
        }
        hero.addView(TextView(this).apply {
            text = "VENDAS 2026"
            textSize = 11f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(Color.WHITE)
            background = roundedBg(Color.argb(65, 255, 255, 255), 24f, Color.argb(85, 255, 255, 255))
            setPadding(14, 8, 14, 8)
        })
        hero.addView(TextView(this).apply {
            text = "Olá, $nome"
            textSize = 28f
            typeface = Typeface.create("sans-serif-medium", Typeface.BOLD)
            setTextColor(Color.WHITE)
            setPadding(0, 16, 0, 6)
        })
        hero.addView(TextView(this).apply {
            text = "${empresaAtiva?.nome ?: "Empresa"}"
            textSize = 14f
            setTextColor(Color.rgb(219, 234, 254))
            setLineSpacing(4f, 1.0f)
        })
        val actionRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(0, 18, 0, 0)
        }
        actionRow.addView(TextView(this).apply {
            text = "Novo pedido"
            textSize = 13f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(azulBotaoEscuro)
            gravity = Gravity.CENTER
            background = roundedBg(Color.WHITE, 28f)
            setPadding(18, 12, 18, 12)
            setOnClickListener { iniciarNovoPedido() }
        }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(0,0,8,0) })
        actionRow.addView(TextView(this).apply {
            text = "Pedidos"
            textSize = 13f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(azulBotaoEscuro)
            gravity = Gravity.CENTER
            background = roundedBg(Color.WHITE, 28f)
            setPadding(18, 12, 18, 12)
            setOnClickListener { loadPedidos() }
        }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(8,0,0,0) })
        hero.addView(actionRow)
        return hero
    }

    private fun showHome() {
        root = baseRoot()
        setScreen(root)
        val nome = usuarioLogado?.nome ?: "Vendedor"
        root.addView(homeHero(nome))
        root.addView(companyContextCard())
        root.addView(kpiRow())
        if (remoteConfig.mensagemHome.isNotBlank()) root.addView(infoBox(remoteConfig.mensagemHome))

        val menu1 = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        menu1.addView(menuIconCard("🛒", remoteConfig.labelNovoPedido, "", true) { iniciarNovoPedido() }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(0, 0, 10, 16) })
        menu1.addView(menuIconCard("📋", remoteConfig.labelPedidos, "", false) { loadPedidos() }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(10, 0, 0, 16) })
        root.addView(menu1)

        val menu2 = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        menu2.addView(menuIconCard("📦", remoteConfig.labelProdutos, "", false) { loadProdutos() }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(0, 0, 10, 16) })
        menu2.addView(menuIconCard("👥", remoteConfig.labelClientes, "", false) { loadClientesConsulta() }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(10, 0, 0, 16) })
        root.addView(menu2)

        val menu3 = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        menu3.addView(menuIconCard("➕", remoteConfig.labelNovoCliente, "", false) { showNovoCliente() }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(0, 0, 10, 16) })
        menu3.addView(menuIconCard("🚚", remoteConfig.labelTransportadora, "", false) { showCadastrarTransportadora() }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(10, 0, 0, 16) })
        root.addView(menu3)

        if (remoteConfig.mostrarNotificacoes || remoteConfig.mostrarRota) {
            val menu4 = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
            if (remoteConfig.mostrarNotificacoes) menu4.addView(menuIconCard("🔔", "Notificações", "", false) { showNotificacoes() }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(0, 0, 10, 16) })
            if (remoteConfig.mostrarRota) menu4.addView(menuIconCard("📍", "Rota", "", false) { showRotaVisitas() }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(10, 0, 0, 16) })
            root.addView(menu4)
        }

        if (remoteConfig.mostrarHistorico || remoteConfig.mostrarCampanhas) {
            val menu5 = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
            if (remoteConfig.mostrarHistorico) menu5.addView(menuIconCard("🕘", "Histórico", "", false) { showHistoricoPedidos() }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(0, 0, 10, 16) })
            if (remoteConfig.mostrarCampanhas) menu5.addView(menuIconCard("🏷️", "Campanhas", "", false) { showCampanhas() }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(10, 0, 0, 16) })
            root.addView(menu5)
        }

        if (remoteConfig.mostrarOffline || remoteConfig.mostrarEmpresa) {
            val menu6 = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
            if (remoteConfig.mostrarOffline) menu6.addView(menuIconCard("🔄", "Offline", "", false) { showSincronizacaoOffline() }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(0, 0, 10, 16) })
            if (remoteConfig.mostrarEmpresa) menu6.addView(menuIconCard("🏢", "Empresa", "", false) { showSelecionarEmpresa(empresasCache.ifEmpty { MockRepository.empresas }) }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(10, 0, 0, 16) })
            root.addView(menu6)
        }

        root.addView(secondaryButton("Sair") { usuarioLogado = null; empresaAtiva = null; showLogin() }, LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, 6, 0, 32) })
    }

    private fun companyContextCard(): View {
        val emp = empresaAtiva
        val texto = if (emp != null) "${emp.nome} • ${emp.cidade.ifBlank { "empresa selecionada" }}" else "Nenhuma empresa selecionada"
        return LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            background = roundedBg(azulSoft, 26f, Color.rgb(191, 219, 254))
            setPadding(18, 14, 18, 14)
            layoutParams = LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, 0, 0, 14) }
            addView(TextView(context).apply { text = "🏢"; textSize = 22f; setPadding(0,0,12,0) })
            addView(TextView(context).apply {
                text = texto
                textSize = 12.5f
                typeface = Typeface.create("sans-serif-medium", Typeface.BOLD)
                setTextColor(azulEscuro)
            }, LinearLayout.LayoutParams(0, -2, 1f))
            addView(TextView(context).apply {
                text = "Trocar"
                textSize = 12f
                typeface = Typeface.DEFAULT_BOLD
                setTextColor(azul)
                setOnClickListener { showSelecionarEmpresa(empresasCache.ifEmpty { MockRepository.empresas }) }
            })
        }
    }

    private fun roundedBg(color: Int, radius: Float = 28f, strokeColor: Int? = null): GradientDrawable {
        return GradientDrawable().apply {
            setColor(color)
            cornerRadius = radius
            strokeColor?.let { setStroke(2, it) }
        }
    }

    private fun gradientBg(startColor: Int, endColor: Int, radius: Float = 36f): GradientDrawable {
        return GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT, intArrayOf(startColor, endColor)).apply {
            cornerRadius = radius
        }
    }

    private fun menuIconCard(icone: String, titulo: String, apoio: String, destaque: Boolean, onClick: () -> Unit): View {
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            background = if (destaque) gradientBg(azulBotao, azulBotaoEscuro, 36f) else roundedBg(Color.WHITE, 36f, bordaWeb)
            setPadding(16, 24, 16, 22)
            minimumHeight = 178
            setOnClickListener { onClick() }
        }
        box.addView(TextView(this).apply {
            text = icone
            textSize = 31f
            gravity = Gravity.CENTER
            setPadding(0, 0, 0, 14)
        })
        box.addView(TextView(this).apply {
            text = titulo
            textSize = if (titulo.length > 12) 14.5f else 16f
            typeface = Typeface.create("sans-serif-medium", Typeface.BOLD)
            gravity = Gravity.CENTER
            setSingleLine(true)
            includeFontPadding = false
            setTextColor(if (destaque) Color.WHITE else azulEscuro)
        })
        if (apoio.isNotBlank()) box.addView(TextView(this).apply {
            text = apoio
            textSize = 13f
            gravity = Gravity.CENTER
            setTextColor(if (destaque) Color.rgb(219, 234, 254) else cinzaTexto)
            setPadding(0, 4, 0, 0)
        })
        return box
    }

    private fun kpiRow(): View {
        val box = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; setPadding(0, 0, 0, 18) }
        box.addView(kpi("${4 + pedidosCriados.size}", "Pedidos"), LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(0,0,8,0) })
        box.addView(kpi("${carrinho.sumOf { it.quantidade }}", "Itens carrinho"), LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(8,0,0,0) })
        return box
    }

    private fun kpi(valor: String, label: String): View = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        background = roundedBg(Color.WHITE, 26f, bordaWeb)
        setPadding(20, 18, 20, 18)
        addView(TextView(context).apply { text = valor; textSize = 28f; typeface = Typeface.DEFAULT_BOLD; setTextColor(azul) })
        addView(TextView(context).apply { text = label; textSize = 13f; setTextColor(cinzaTexto) })
    }

    private fun card(titulo: String, desc: String, btn: String, onClick: () -> Unit): View {
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            background = roundedBg(Color.WHITE, 32f, bordaWeb)
            setPadding(28, 24, 28, 24)
            layoutParams = LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, 0, 0, 20) }
        }
        box.addView(TextView(this).apply { text = titulo; textSize = 20f; typeface = Typeface.DEFAULT_BOLD; setTextColor(azulEscuro); setPadding(0, 0, 0, if (desc.isBlank()) 12 else 0) })
        if (desc.isNotBlank()) box.addView(TextView(this).apply { text = desc; textSize = 14f; setTextColor(cinzaTexto); setPadding(0, 6, 0, 12) })
        box.addView(button(btn, onClick))
        return box
    }



    private fun featureCard(icone: String, titulo: String, desc: String, btn: String, onClick: () -> Unit): View {
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            background = roundedBg(Color.WHITE, 32f, bordaWeb)
            setPadding(24, 20, 24, 20)
            layoutParams = LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, 0, 0, 16) }
        }
        val row = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
        row.addView(TextView(this).apply {
            text = icone
            textSize = 28f
            gravity = Gravity.CENTER
            background = roundedBg(azulSoft, 24f, Color.rgb(191, 219, 254))
            setPadding(14, 10, 14, 10)
        })
        row.addView(LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(16, 0, 0, 0)
            addView(TextView(context).apply { text = titulo; textSize = 17f; typeface = Typeface.create("sans-serif-medium", Typeface.BOLD); setTextColor(azulEscuro) })
            addView(TextView(context).apply { text = desc; textSize = 13f; setTextColor(cinzaTexto); setPadding(0, 4, 0, 0) })
        }, LinearLayout.LayoutParams(0, -2, 1f))
        box.addView(row)
        box.addView(secondaryButton(btn) { onClick() }, LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, 14, 0, 0) })
        return box
    }

    private fun showNotificacoes() {
        root = baseRoot(); setScreen(root)
        root.addView(topBackBar("Notificações") { showHome() })
        root.addView(title("Notificações"))
        root.addView(featureCard("✅", "Pedido aprovado", "O pedido 000129 foi aprovado e está liberado para sequência.", "Ver pedidos") { loadPedidos() })
        root.addView(featureCard("📦", "Produto em destaque", "Carrinho Infantil Premium com boa disponibilidade para venda.", "Ver produtos") { loadProdutos() })
        root.addView(featureCard("🏷️", "Campanha ativa", "Condição especial para mix de brinquedos nesta empresa.", "Ver campanhas") { showCampanhas() })
        root.addView(featureCard("🔄", "Status em tempo real", "Atualize a carteira e veja aprovações, integrações e pendências.", "Atualizar status") { loadPedidos() })
        root.addView(secondaryButton("Voltar") { showHome() })
    }

    private fun showRotaVisitas() {
        root = baseRoot(); setScreen(root)
        root.addView(topBackBar("Rota") { showHome() })
        root.addView(title("Rota de visitas"))
        root.addView(featureCard("📍", "Mercado Nova Era", "Santo André/SP • Próxima visita sugerida", "Registrar check-in") { Toast.makeText(this, "Check-in registrado no app", Toast.LENGTH_LONG).show() })
        root.addView(featureCard("📍", "Distribuidora Alfa", "São Bernardo/SP • Cliente com pedido recente", "Abrir cliente") { loadClientesConsulta() })
        root.addView(featureCard("📍", "Atacado Kids Brasil", "Guarulhos/SP • Revisar oportunidades", "Novo pedido") { iniciarNovoPedido() })
        root.addView(secondaryButton("Voltar") { showHome() })
    }

    private fun showLeitorCodigo() {
        root = baseRoot(); setScreen(root)
        root.addView(topBackBar("Leitor") { showHome() })
        root.addView(title("Leitor de código"))
        root.addView(subtitle("Informe ou cole o código de barras/SKU para localizar o produto."))
        val codigo = premiumInput("Código", "Digite ou escaneie o código")
        root.addView(formSection("Buscar produto", "▦", labeledField("Código / SKU", codigo)))
        root.addView(button("Consultar produto") {
            val q = codigo.text.toString().trim()
            if (q.isBlank()) Toast.makeText(this, "Informe o código", Toast.LENGTH_SHORT).show()
            else {
                val lista = if (produtosCache.isNotEmpty()) produtosCache else MockRepository.produtos(empresaIdAtiva())
                val encontrados = lista.filter { it.codigo.contains(q, true) || it.nome.contains(q, true) }
                if (encontrados.isEmpty()) Toast.makeText(this, "Produto não encontrado", Toast.LENGTH_LONG).show() else showProdutos(encontrados)
            }
        })
        root.addView(secondaryButton("Voltar") { showHome() })
    }

    private fun showHistoricoPedidos() {
        root = baseRoot(); setScreen(root)
        root.addView(topBackBar("Histórico") { showHome() })
        root.addView(title("Histórico de pedidos"))
        val pedidos = pedidosCriados + MockRepository.pedidos(empresaIdAtiva())
        pedidos.forEach { p -> root.addView(card("Pedido ${p.numero}", "${p.cliente} • ${p.status} • ${p.total}", "Consultar") { Toast.makeText(this, "Consulta do pedido ${p.numero}", Toast.LENGTH_SHORT).show() }) }
        root.addView(secondaryButton("Voltar") { showHome() })
    }

    private fun showCampanhas() {
        root = baseRoot(); setScreen(root)
        root.addView(topBackBar("Campanhas") { showHome() })
        root.addView(title("Campanhas"))
        root.addView(featureCard("🏷️", "Mix brinquedos", "Condição comercial para pedidos com 5 ou mais itens.", "Criar pedido") { iniciarNovoPedido() })
        root.addView(featureCard("%", "Desconto controlado", "O desconto continua respeitando a regra comercial do ERP.", "Novo pedido") { iniciarNovoPedido() })
        root.addView(secondaryButton("Voltar") { showHome() })
    }

    private fun loadClientesConsulta() {
        showLoading("Carregando clientes...")
        Thread {
            val result = MobileRepository.clientes(usuarioLogado?.token ?: "")
            runOnUiThread {
                if (result.ok && result.data != null) {
                    clientesCache = clientesCriados + result.data
                    showClientesConsulta(clientesCache)
                } else showError(result.message, ::showHome)
            }
        }.start()
    }

    private fun showClientesConsulta(clientes: List<ClienteResumo>) {
        root = baseRoot(); setScreen(root)
        root.addView(topBackBar("Clientes") { showHome() })
        root.addView(title("Clientes"))
        root.addView(subtitle("Consulta e edição em layout premium, seguindo o mesmo padrão visual dos cadastros."))
        root.addView(premiumSearchBox("Buscar por código, nome ou cidade", { q ->
            val filtrados = if (q.isBlank()) clientesCache else clientesCache.filter { it.codigo.contains(q, true) || it.nome.contains(q, true) || it.cidade.contains(q, true) }
            showClientesConsulta(filtrados)
        }, { showClientesConsulta(clientesCache) }))
        root.addView(sectionLabel("Consulta e edição"))
        if (clientes.isEmpty()) root.addView(card("Nenhum cliente encontrado", "Tente buscar por outro código, nome ou cidade.", "Voltar") { showHome() })
        clientes.forEach { c -> root.addView(clienteConsultaCard(c)) }
        root.addView(secondaryButton("Voltar ao menu") { showHome() })
    }

    private fun clienteConsultaCard(c: ClienteResumo): View {
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            background = roundedBg(Color.WHITE, 32f, bordaWeb)
            setPadding(22, 18, 22, 18)
            layoutParams = LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, 0, 0, 18) }
        }
        val topo = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
        topo.addView(TextView(this).apply {
            text = "👤"
            textSize = 28f
            gravity = Gravity.CENTER
            background = roundedBg(azulSoft, 24f, Color.rgb(191, 219, 254))
            setPadding(16, 10, 16, 10)
        })
        topo.addView(LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(16, 0, 0, 0)
            addView(TextView(context).apply { text = c.nome; textSize = 18f; typeface = Typeface.DEFAULT_BOLD; setTextColor(azulEscuro) })
            addView(TextView(context).apply { text = "Código ${c.codigo}"; textSize = 13f; setTextColor(cinzaTexto) })
        }, LinearLayout.LayoutParams(0, -2, 1f))
        box.addView(topo)
        box.addView(twoColumns(
            miniInfo("Cidade/UF", c.cidade),
            miniInfo("Status", "Ativo")
        ))
        box.addView(button("Consultar / editar") { showEditarCliente(c) })
        return box
    }

    private fun showEditarCliente(c: ClienteResumo) {
        root = baseRoot(); setScreen(root)
        root.addView(topBackBar("Editar cliente") { showClientesConsulta(clientesCache) })
        root.addView(title("Editar cliente"))
        root.addView(subtitle("Edição local/segura com o mesmo layout premium do cadastro."))
        root.addView(infoBox("Nesta etapa a edição fica salva no app. Depois conectamos o botão Salvar na API real para atualizar o ERP Web."))
        val codigo = premiumInput("Código", "Código", enabled = false).apply { setText(c.codigo) }
        val nome = premiumInput("Nome do cliente", "Nome fantasia / razão social").apply { setText(c.nome) }
        val cidade = premiumInput("Cidade/UF", "Cidade / UF").apply { setText(c.cidade) }
        val email = premiumInput("E-mail de cobrança", "financeiro@cliente.com", InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS)
        val telefone = premiumInput("Telefone", "(00) 00000-0000")
        val status = premiumInput("Status", "Ativo").apply { setText("Ativo") }
        root.addView(formSection("Identificação", "👤",
            twoColumns(labeledField("Código", codigo), labeledField("Status", status)),
            labeledField("Nome do cliente", nome)
        ))
        root.addView(formSection("Contato e região", "📍",
            twoColumns(labeledField("Cidade/UF", cidade), labeledField("Telefone", telefone)),
            labeledField("E-mail de cobrança", email)
        ))
        root.addView(button("Salvar edição") {
            val atualizado = ClienteResumo(c.codigo, nome.text.toString().ifBlank { c.nome }, cidade.text.toString().ifBlank { c.cidade })
            clientesCriados.removeAll { it.codigo == c.codigo }
            clientesCriados.add(0, atualizado)
            clientesCache = clientesCache.map { if (it.codigo == c.codigo) atualizado else it }
            Toast.makeText(this, "Cliente atualizado no app", Toast.LENGTH_LONG).show()
            showClientesConsulta(clientesCache)
        })
        root.addView(secondaryButton("Voltar para clientes") { showClientesConsulta(clientesCache) })
    }

    private fun showNovoCliente() {
        root = baseRoot(); setScreen(root)
        root.addView(topBackBar("Novo cliente") { showHome() })
        root.addView(title("Novo cliente"))

        val codigo = premiumInput("Código", "C${900 + clientesCriados.size + 1}").apply { setText("C${900 + clientesCriados.size + 1}") }
        val cnpj = premiumInput("CNPJ", "00.000.000/0000-00", InputType.TYPE_CLASS_NUMBER)
        val fantasia = premiumInput("Nome fantasia", "Nome comercial do cliente")
        val nome = premiumInput("Razão social", "Razão social do CNPJ")
        val endereco = premiumInput("Endereço", "Endereço completo", InputType.TYPE_CLASS_TEXT, true, 2)
        val cidade = premiumInput("Cidade/UF", "Cidade / UF")
        val ie = premiumInput("Inscrição estadual", "Preenchimento automático por CNPJ")
        val suframa = premiumInput("SUFRAMA", "SUFRAMA, se houver")
        val emailGeral = premiumInput("E-mail geral", "email@cliente.com", InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS)
        val telefone = premiumInput("Telefone", "(00) 00000-0000")
        val emailCobranca = premiumInput("E-mail de cobrança", "financeiro@cliente.com", InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS)
        val status = premiumInput("Status", "Ativo").apply { setText("Ativo") }

        root.addView(formSection("Consulta do CNPJ", "🔎",
            twoColumns(labeledField("Código", codigo), labeledField("CNPJ", cnpj)),
            button("Buscar dados pelo CNPJ") {
                buscarCnpj(cnpj.text.toString(), "cliente") { dados ->
                    preencherSeVazio(nome, dados["razao"])
                    preencherSeVazio(fantasia, dados["fantasia"])
                    preencherSeVazio(endereco, dados["endereco"])
                    preencherSeVazio(cidade, dados["cidadeUf"])
                    preencherSeVazio(ie, dados["ie"])
                    preencherSeVazio(suframa, dados["suframa"])
                    preencherSeVazio(telefone, dados["telefone"])
                }
            }
        ))

        root.addView(formSection("Dados comerciais", "🏢",
            twoColumns(labeledField("Nome fantasia / Nome comercial", fantasia), labeledField("Razão social", nome)),
            twoColumns(labeledField("E-mail geral", emailGeral), labeledField("Telefone", telefone))
        ))

        root.addView(formSection("Endereço e fiscal", "📍",
            labeledField("Endereço completo", endereco),
            twoColumns(labeledField("Cidade/UF", cidade), labeledField("Inscrição Estadual", ie)),
            labeledField("SUFRAMA, se houver", suframa)
        ))

        root.addView(formSection("Financeiro", "💰",
            twoColumns(labeledField("E-mail de cobrança", emailCobranca), labeledField("Status", status))
        ))

        root.addView(button("Salvar cliente") {
            if (cnpj.text.isBlank() || nome.text.isBlank() || cidade.text.isBlank() || emailCobranca.text.isBlank()) {
                Toast.makeText(this, "Preencha os campos obrigatórios", Toast.LENGTH_SHORT).show()
                return@button
            }
            val novo = ClienteResumo(codigo.text.toString().ifBlank { "C${900 + clientesCriados.size + 1}" }, nome.text.toString(), cidade.text.toString())
            clientesCriados.add(0, novo)
            clientesCache = clientesCriados + clientesCache.filter { it.codigo != novo.codigo }
            Toast.makeText(this, "Cliente cadastrado", Toast.LENGTH_LONG).show()
            showClientesConsulta(clientesCache)
        })
        root.addView(secondaryButton("Voltar ao menu") { showHome() })
    }

    private fun showCadastrarTransportadora() {
        root = baseRoot(); setScreen(root)
        root.addView(topBackBar("Transportadora") { showHome() })
        root.addView(title("Cadastrar transportadora"))

        val codigo = premiumInput("Código", "T${900 + transportadorasCriadas.size + 1}").apply { setText("T${900 + transportadorasCriadas.size + 1}") }
        val cnpj = premiumInput("CNPJ", "00.000.000/0000-00", InputType.TYPE_CLASS_NUMBER)
        val nome = premiumInput("Nome da transportadora", "Transportadora / Razão social")
        val endereco = premiumInput("Endereço", "Endereço completo", InputType.TYPE_CLASS_TEXT, true, 2)
        val telefone = premiumInput("Telefone", "Telefone de contato")
        val regiao = premiumInput("Região", "Região de atendimento")

        root.addView(formSection("Consulta da transportadora", "🚚",
            twoColumns(labeledField("Código", codigo), labeledField("CNPJ", cnpj)),
            button("Buscar transportadora pelo CNPJ") {
                buscarCnpj(cnpj.text.toString(), "transportadora") { dados ->
                    preencherSeVazio(nome, dados["razao"] ?: dados["fantasia"])
                    preencherSeVazio(endereco, dados["endereco"])
                    preencherSeVazio(telefone, dados["telefone"])
                    preencherSeVazio(regiao, dados["cidadeUf"])
                }
            }
        ))

        root.addView(formSection("Dados da transportadora", "📦",
            labeledField("Nome / Razão social", nome),
            labeledField("Endereço completo", endereco),
            twoColumns(labeledField("Telefone de contato", telefone), labeledField("Região", regiao))
        ))

        root.addView(button("Salvar transportadora") {
            if (cnpj.text.isBlank() || nome.text.isBlank() || endereco.text.isBlank()) {
                Toast.makeText(this, "Preencha os campos obrigatórios", Toast.LENGTH_SHORT).show()
                return@button
            }
            val nova = TransportadoraResumo(
                codigo.text.toString().ifBlank { "T${900 + transportadorasCriadas.size + 1}" },
                nome.text.toString(),
                regiao.text.toString().ifBlank { "Região não informada" },
                telefone.text.toString().ifBlank { "Telefone não informado" }
            )
            transportadorasCriadas.add(0, nova)
            transportadorasCache = transportadorasCriadas + transportadorasCache.filter { it.codigo != nova.codigo }
            Toast.makeText(this, "Transportadora cadastrada no app", Toast.LENGTH_LONG).show()
            showHome()
        })
        root.addView(secondaryButton("Voltar ao menu") { showHome() })
    }

    private fun somenteNumeros(valor: String): String = valor.filter { it.isDigit() }

    private fun preencherSeVazio(campo: EditText, valor: String?) {
        if (!valor.isNullOrBlank() && campo.text.isBlank()) campo.setText(valor)
    }

    private fun buscarCnpj(cnpjInformado: String, tipo: String, aoEncontrar: (Map<String, String>) -> Unit) {
        val cnpj = somenteNumeros(cnpjInformado)
        if (cnpj.length != 14) {
            Toast.makeText(this, "Informe um CNPJ válido com 14 números", Toast.LENGTH_SHORT).show()
            return
        }
        Toast.makeText(this, "Consultando CNPJ...", Toast.LENGTH_SHORT).show()
        Thread {
            val dados = consultarCnpjWs(cnpj).ifEmpty { consultarBrasilApi(cnpj) }
            runOnUiThread {
                if (dados.isEmpty()) {
                    Toast.makeText(this, "Não consegui consultar esse CNPJ agora. Os campos continuam editáveis.", Toast.LENGTH_LONG).show()
                } else {
                    aoEncontrar(dados)
                    val msg = if (tipo == "cliente") "Dados do cliente preenchidos" else "Dados da transportadora preenchidos"
                    Toast.makeText(this, msg, Toast.LENGTH_LONG).show()
                }
            }
        }.start()
    }

    private fun getJson(urlText: String): JSONObject? {
        return try {
            val conn = (URL(urlText).openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                connectTimeout = 10000
                readTimeout = 10000
                setRequestProperty("Accept", "application/json")
                setRequestProperty("User-Agent", "Vendas2026Mobile/1.0")
            }
            val stream = if (conn.responseCode in 200..299) conn.inputStream else conn.errorStream
            val body = stream.bufferedReader().use { it.readText() }
            conn.disconnect()
            if (body.isBlank() || !body.trim().startsWith("{")) null else JSONObject(body)
        } catch (_: Exception) { null }
    }

    private fun valorValido(valor: String?): String {
        val v = valor?.trim().orEmpty()
        return if (v.isBlank() || v.equals("null", true) || v == "0") "" else v
    }

    private fun primeiroCampoValido(obj: JSONObject?, vararg campos: String): String {
        if (obj == null) return ""
        campos.forEach { campo ->
            val v = valorValido(obj.optString(campo))
            if (v.isNotBlank()) return v
        }
        return ""
    }

    private fun primeiroCampoArrayValido(array: org.json.JSONArray?, vararg campos: String): String {
        if (array == null) return ""
        for (i in 0 until array.length()) {
            val item = array.optJSONObject(i) ?: continue
            val v = primeiroCampoValido(item, *campos)
            if (v.isNotBlank()) return v
        }
        return ""
    }

    private fun consultarBrasilApi(cnpj: String): Map<String, String> {
        val json = getJson("https://brasilapi.com.br/api/cnpj/v1/$cnpj") ?: return emptyMap()
        val logradouro = listOf(json.optString("descricao_tipo_de_logradouro"), json.optString("logradouro"), json.optString("numero"))
            .filter { it.isNotBlank() }.joinToString(" ")
        val complemento = json.optString("complemento")
        val bairro = json.optString("bairro")
        val cidade = json.optString("municipio")
        val uf = json.optString("uf")
        val cep = json.optString("cep")
        val endereco = listOf(logradouro, complemento, bairro, "CEP $cep").filter { it.isNotBlank() && it != "CEP " }.joinToString(" - ")
        val suframa = primeiroCampoValido(json, "suframa", "inscricao_suframa", "codigo_suframa")
        return mapOf(
            "razao" to json.optString("razao_social"),
            "fantasia" to json.optString("nome_fantasia"),
            "endereco" to endereco,
            "cidadeUf" to listOf(cidade, uf).filter { it.isNotBlank() }.joinToString("/"),
            "telefone" to json.optString("ddd_telefone_1"),
            "ie" to primeiroCampoValido(json, "inscricao_estadual", "ie"),
            "suframa" to suframa
        ).filterValues { it.isNotBlank() }
    }

    private fun consultarCnpjWs(cnpj: String): Map<String, String> {
        val json = getJson("https://publica.cnpj.ws/cnpj/$cnpj") ?: return emptyMap()
        val est = json.optJSONObject("estabelecimento") ?: return emptyMap()
        val cidadeObj = est.optJSONObject("cidade")
        val estadoObj = est.optJSONObject("estado")
        val logradouro = listOf(est.optString("tipo_logradouro"), est.optString("logradouro"), est.optString("numero"))
            .filter { it.isNotBlank() }.joinToString(" ")
        val endereco = listOf(logradouro, est.optString("complemento"), est.optString("bairro"), "CEP ${est.optString("cep")}")
            .filter { it.isNotBlank() && it != "CEP " }.joinToString(" - ")
        val inscricoes = est.optJSONArray("inscricoes_estaduais")
        val ie = primeiroCampoArrayValido(inscricoes, "inscricao_estadual", "inscricao", "numero")
        val suframa = listOf(
            primeiroCampoValido(est, "inscricao_suframa", "suframa", "codigo_suframa"),
            primeiroCampoArrayValido(est.optJSONArray("inscricoes_suframa"), "inscricao_suframa", "suframa", "codigo", "numero"),
            primeiroCampoArrayValido(json.optJSONArray("inscricoes_suframa"), "inscricao_suframa", "suframa", "codigo", "numero"),
            primeiroCampoValido(json, "inscricao_suframa", "suframa", "codigo_suframa")
        ).firstOrNull { it.isNotBlank() } ?: ""
        return mapOf(
            "razao" to json.optString("razao_social"),
            "fantasia" to est.optString("nome_fantasia"),
            "endereco" to endereco,
            "cidadeUf" to listOf(cidadeObj?.optString("nome") ?: "", estadoObj?.optString("sigla") ?: "").filter { it.isNotBlank() }.joinToString("/"),
            "telefone" to listOf(est.optString("ddd1"), est.optString("telefone1")).filter { it.isNotBlank() }.joinToString(" "),
            "ie" to ie,
            "suframa" to suframa
        ).filterValues { it.isNotBlank() }
    }

    private fun iniciarNovoPedido() {
        clienteSelecionado = null
        transportadoraSelecionada = null
        condicaoPagamentoSelecionada = null
        observacaoPedido = ""
        carrinho.clear()
        loadClientesParaPedido()
    }

    private fun loadClientesParaPedido() {
        showLoading("Carregando clientes...")
        Thread {
            val result = MobileRepository.clientes(usuarioLogado?.token ?: "")
            runOnUiThread {
                if (result.ok && result.data != null) { clientesCache = clientesCriados + result.data; showSelecionarCliente(clientesCache) }
                else showError(result.message, ::showHome)
            }
        }.start()
    }

    private fun showSelecionarCliente(clientes: List<ClienteResumo>) {
        root = baseRoot(); setScreen(root)
        root.addView(topBackBar("Novo pedido") { showHome() })
        root.addView(pedidoHeader(1, "1. Escolha o cliente", ""))
        root.addView(sectionLabel("Busca rápida"))
        val busca = EditText(this).apply { hint = "Digite código, nome ou cidade"; setSingleLine(true) }
        root.addView(busca)
        val rowBusca = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        rowBusca.addView(button("Buscar") {
            val q = busca.text.toString().trim()
            val filtrados = if (q.isBlank()) clientesCache else clientesCache.filter { it.codigo.contains(q, true) || it.nome.contains(q, true) || it.cidade.contains(q, true) }
            showSelecionarCliente(filtrados)
        }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(0,0,8,0) })
        rowBusca.addView(secondaryButton("Limpar") { showSelecionarCliente(clientesCache) }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(8,0,0,0) })
        root.addView(rowBusca)
        root.addView(sectionLabel("Clientes"))
        clientes.forEach { c -> root.addView(clienteCard(c)) }
        root.addView(secondaryButton("Cancelar pedido") { showHome() })
    }

    private fun clienteCard(c: ClienteResumo): View = card("${c.codigo} - ${c.nome}", c.cidade, "Selecionar cliente") {
        clienteSelecionado = c
        loadTransportadorasParaPedido()
    }

    private fun loadTransportadorasParaPedido() {
        showLoading("Carregando transportadoras...")
        Thread {
            val result = MobileRepository.transportadoras(usuarioLogado?.token ?: "")
            runOnUiThread {
                if (result.ok && result.data != null) { transportadorasCache = transportadorasCriadas + result.data; showSelecionarTransportadora(transportadorasCache) }
                else showError(result.message, ::showHome)
            }
        }.start()
    }

    private fun showSelecionarTransportadora(transportadoras: List<TransportadoraResumo>) {
        root = baseRoot(); setScreen(root)
        root.addView(topBackBar("Transportadora") { showSelecionarCliente(clientesCache) })
        root.addView(pedidoHeader(2, "2. Escolha a transportadora", ""))
        root.addView(resumoPedidoCard(false))
        root.addView(sectionLabel("Busca rápida"))
        val busca = EditText(this).apply { hint = "Buscar por código, nome ou prazo"; setSingleLine(true) }
        root.addView(busca)
        val rowBusca = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        rowBusca.addView(button("Buscar") {
            val q = busca.text.toString().trim()
            val filtrados = if (q.isBlank()) transportadorasCache else transportadorasCache.filter { it.codigo.contains(q, true) || it.nome.contains(q, true) || it.prazo.contains(q, true) }
            showSelecionarTransportadora(filtrados)
        }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(0,0,8,0) })
        rowBusca.addView(secondaryButton("Limpar") { showSelecionarTransportadora(transportadorasCache) }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(8,0,0,0) })
        root.addView(rowBusca)
        root.addView(sectionLabel("Transportadoras"))
        transportadoras.forEach { t -> root.addView(transportadoraCard(t)) }
        root.addView(secondaryButton("Voltar para clientes") { showSelecionarCliente(clientesCache) })
    }

    private fun transportadoraCard(t: TransportadoraResumo): View = card("${t.codigo} - ${t.nome}", "Prazo: ${t.prazo} • Frete: ${t.frete}", "Selecionar transportadora") {
        transportadoraSelecionada = t
        carregarCondicoesPagamento()
    }

    private fun carregarCondicoesPagamento() {
        showLoading("Carregando condições de pagamento...")
        Thread {
            val result = MobileRepository.condicoesPagamento(usuarioLogado?.token ?: "")
            runOnUiThread {
                if (result.ok && result.data != null) { condicoesPagamentoCache = result.data; showSelecionarCondicaoPagamento(result.data) }
                else showError(result.message.ifBlank { "Erro ao carregar condições de pagamento" }) { showSelecionarTransportadora(transportadorasCache) }
            }
        }.start()
    }

    private fun showSelecionarCondicaoPagamento(condicoes: List<CondicaoPagamentoResumo>) {
        root = baseRoot(); setScreen(root)
        root.addView(topBackBar("Pagamento") { showSelecionarTransportadora(transportadorasCache) })
        root.addView(pedidoHeader(3, "3. Escolha a condição de pagamento", ""))
        root.addView(resumoPedidoCard())

        root.addView(sectionLabel("Busca rápida"))
        val busca = EditText(this).apply { hint = "Buscar por código, descrição ou prazo"; setSingleLine(true) }
        root.addView(busca)
        val rowBusca = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        rowBusca.addView(button("Buscar") {
            val q = busca.text.toString().trim()
            val filtrados = if (q.isBlank()) condicoesPagamentoCache else condicoesPagamentoCache.filter { it.codigo.contains(q, true) || it.descricao.contains(q, true) || it.prazo.contains(q, true) }
            showSelecionarCondicaoPagamento(filtrados)
        }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(0,0,8,0) })
        rowBusca.addView(secondaryButton("Limpar") { showSelecionarCondicaoPagamento(condicoesPagamentoCache) }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(8,0,0,0) })
        root.addView(rowBusca)

        root.addView(sectionLabel("Condições de pagamento"))
        condicoes.forEach { c -> root.addView(condicaoPagamentoCard(c)) }
        root.addView(secondaryButton("Voltar para transportadora") { showSelecionarTransportadora(transportadorasCache) })
    }

    private fun condicaoPagamentoCard(c: CondicaoPagamentoResumo): View = card("${c.codigo} - ${c.descricao}", "Prazo: ${c.prazo}", "Selecionar pagamento") {
        condicaoPagamentoSelecionada = c
        loadProdutosParaPedido()
    }

    private fun loadProdutosParaPedido() {
        showLoading("Carregando produtos...")
        Thread {
            val result = MobileRepository.produtos(usuarioLogado?.token ?: "", empresaIdAtiva())
            runOnUiThread {
                if (result.ok && result.data != null) { produtosCache = result.data; showMontarCarrinho(result.data) }
                else showError(result.message, ::showHome)
            }
        }.start()
    }

    private fun showMontarCarrinho(produtos: List<ProdutoResumo>, focarLeitor: Boolean = false) {
        root = baseRoot(); setScreen(root)
        root.addView(topBackBar("Itens") { showSelecionarCondicaoPagamento(condicoesPagamentoCache) })
        root.addView(pedidoHeader(4, "4. Adicione os itens", ""))
        root.addView(resumoPedidoCard(true))

        root.addView(sectionLabel("Adicionar produto"))
        val codigoSku = EditText(this).apply {
            hint = "Digite SKU, nome ou leia QR/código"
            setSingleLine(true)
            inputType = InputType.TYPE_CLASS_TEXT
            imeOptions = android.view.inputmethod.EditorInfo.IME_ACTION_DONE
            setPadding(24, 18, 24, 18)
        }
        codigoSku.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == android.view.inputmethod.EditorInfo.IME_ACTION_DONE) {
                adicionarSkuAoCarrinho(codigoSku.text.toString(), codigoSku)
                true
            } else false
        }
        root.addView(codigoSku)

        val rowLeitor = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        rowLeitor.addView(button("Adicionar / Ler código") {
            adicionarSkuAoCarrinho(codigoSku.text.toString(), codigoSku)
        }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(0,0,8,0) })
        rowLeitor.addView(secondaryButton("Limpar") { codigoSku.setText(""); codigoSku.requestFocus() }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(8,0,0,0) })
        root.addView(rowLeitor)

        root.addView(TextView(this).apply {
            text = "Use o mesmo campo para digitar, colar ou ler o código. Após adicionar, o campo limpa e fica pronto para o próximo item."
            textSize = 12f
            setTextColor(cinzaTexto)
            setPadding(6, 6, 6, 14)
        })

        root.addView(sectionLabel("Sugestões rápidas"))
        val busca = EditText(this).apply { hint = "Filtrar por SKU, nome ou código de barras"; setSingleLine(true) }
        root.addView(busca)
        val rowBusca = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        rowBusca.addView(button("Filtrar") {
            val q = busca.text.toString().trim()
            val filtrados = if (q.isBlank()) produtosCache else produtosCache.filter { it.codigo.contains(q, true) || it.nome.contains(q, true) || it.descricao.contains(q, true) }
            showMontarCarrinho(filtrados)
        }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(0,0,8,0) })
        rowBusca.addView(secondaryButton("Limpar") { showMontarCarrinho(produtosCache) }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(8,0,0,0) })
        root.addView(rowBusca)
        if (focarLeitor) codigoSku.post { codigoSku.requestFocus() }
        root.addView(sectionLabel("Produtos"))
        produtos.forEach { p -> root.addView(produtoPedidoCard(p)) }
        root.addView(successButton("Finalizar no carrinho") { showCarrinho() })
        root.addView(secondaryButton("Voltar para pagamento") { showSelecionarCondicaoPagamento(condicoesPagamentoCache) })
    }

    private fun adicionarSkuAoCarrinho(codigoLido: String, campoSku: EditText) {
        val q = codigoLido.trim()
        if (q.isBlank()) {
            Toast.makeText(this, "Informe ou leia o SKU/código de barras", Toast.LENGTH_SHORT).show()
            campoSku.requestFocus()
            return
        }
        val lista = if (produtosCache.isNotEmpty()) produtosCache else MockRepository.produtos(empresaIdAtiva())
        val produto = lista.firstOrNull { it.codigo.equals(q, true) }
            ?: lista.firstOrNull { it.codigo.contains(q, true) || it.nome.contains(q, true) }
        if (produto == null) {
            Toast.makeText(this, "Produto não encontrado para o código $q", Toast.LENGTH_LONG).show()
            campoSku.selectAll()
            campoSku.requestFocus()
            return
        }
        if (produto.estoque <= 0) {
            Toast.makeText(this, "Produto sem estoque: ${produto.nome}", Toast.LENGTH_LONG).show()
            campoSku.setText("")
            campoSku.requestFocus()
            return
        }
        val item = carrinho.firstOrNull { it.produto.codigo == produto.codigo && it.descontoPercentual == 0.0 }
        if (item == null) carrinho.add(CarrinhoItem(produto, 1, 0.0)) else item.quantidade += 1
        Toast.makeText(this, "${produto.nome} adicionado. Leia o próximo item.", Toast.LENGTH_SHORT).show()
        campoSku.setText("")
        showMontarCarrinho(produtosCache.ifEmpty { lista }, true)
    }

    private fun produtoPedidoCard(p: ProdutoResumo): View {
        val precoUnitario = parseCurrency(p.preco)
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.WHITE)
            setPadding(28, 22, 28, 22)
            layoutParams = LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, 0, 0, 18) }
        }

        box.addView(TextView(this).apply {
            text = "${p.codigo} - ${p.nome}"
            textSize = 18f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(azulEscuro)
        })
        box.addView(TextView(this).apply {
            text = "Unitário: ${p.preco} • Estoque: ${p.estoque}"
            textSize = 14f
            setTextColor(if (p.estoque > 0) cinzaTexto else vermelho)
            setPadding(0, 6, 0, 12)
        })

        if (p.estoque <= 0) {
            box.addView(secondaryButton("Indisponível") { Toast.makeText(this, "Produto sem estoque", Toast.LENGTH_SHORT).show() })
            return box
        }

        val row = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        val qtdInput = EditText(this).apply {
            hint = "Qtd"
            setText("1")
            inputType = InputType.TYPE_CLASS_NUMBER
            setSingleLine(true)
        }
        val descontoInput = EditText(this).apply {
            hint = "Desc. %"
            setText("0")
            inputType = InputType.TYPE_CLASS_NUMBER or InputType.TYPE_NUMBER_FLAG_DECIMAL
            setSingleLine(true)
        }
        row.addView(qtdInput, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(0,0,8,0) })
        row.addView(descontoInput, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(8,0,0,0) })
        box.addView(row)

        val resumo = TextView(this).apply {
            textSize = 15f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(verde)
            setPadding(0, 12, 0, 12)
        }
        box.addView(resumo)

        fun atualizarResumo() {
            val qtd = qtdInput.text.toString().toIntOrNull()?.coerceAtLeast(1) ?: 1
            val desconto = descontoInput.text.toString().replace(",", ".").toDoubleOrNull()?.coerceIn(0.0, 100.0) ?: 0.0
            val unitComDesconto = precoUnitario * (1 - desconto / 100.0)
            val total = unitComDesconto * qtd
            resumo.text = "Com desconto: ${formatCurrency(unitComDesconto)} un. • Total: ${formatCurrency(total)}"
        }

        val watcher = object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) { atualizarResumo() }
            override fun afterTextChanged(s: Editable?) {}
        }
        qtdInput.addTextChangedListener(watcher)
        descontoInput.addTextChangedListener(watcher)
        atualizarResumo()

        box.addView(button("Adicionar ao carrinho") {
            val qtd = qtdInput.text.toString().toIntOrNull()?.coerceAtLeast(1) ?: 1
            val desconto = descontoInput.text.toString().replace(",", ".").toDoubleOrNull()?.coerceIn(0.0, 100.0) ?: 0.0
            if (qtd > p.estoque) {
                Toast.makeText(this, "Quantidade maior que o estoque disponível", Toast.LENGTH_LONG).show()
                return@button
            }
            val item = carrinho.firstOrNull { it.produto.codigo == p.codigo && it.descontoPercentual == desconto }
            if (item == null) carrinho.add(CarrinhoItem(p, qtd, desconto)) else item.quantidade += qtd
            Toast.makeText(this, "Produto adicionado ao carrinho", Toast.LENGTH_SHORT).show()
            showMontarCarrinho(produtosCache)
        })
        return box
    }

    private fun showCarrinho() {
        root = baseRoot(); setScreen(root)
        root.addView(topBackBar("Carrinho") { showMontarCarrinho(produtosCache) })
        root.addView(pedidoHeader(5, "5. Revise e conclua", ""))
        root.addView(resumoPedidoCard(false))
        root.addView(card("Cliente", clienteSelecionado?.nome ?: "Nenhum cliente selecionado", "Trocar cliente") { showSelecionarCliente(clientesCache) })
        root.addView(card("Transportadora", transportadoraSelecionada?.let { "${it.nome} • ${it.prazo} • ${it.frete}" } ?: "Nenhuma transportadora selecionada", "Trocar transportadora") { showSelecionarTransportadora(transportadorasCache) })
        root.addView(card("Condição de pagamento", condicaoPagamentoSelecionada?.let { "${it.codigo} - ${it.descricao} • ${it.prazo}" } ?: "Nenhuma condição selecionada", "Trocar pagamento") { showSelecionarCondicaoPagamento(condicoesPagamentoCache) })
        root.addView(sectionLabel("Observação do pedido"))
        val obsInput = EditText(this).apply {
            hint = "Ex.: entregar pela manhã, pedido de feira, observação comercial..."
            setText(observacaoPedido)
            minLines = 3
            gravity = Gravity.TOP
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_MULTI_LINE
        }
        root.addView(obsInput)
        if (carrinho.isEmpty()) {
            root.addView(card("Carrinho vazio", "Adicione produtos antes de enviar.", "Adicionar produtos") { showMontarCarrinho(produtosCache) })
        } else {
            root.addView(sectionLabel("Itens do carrinho"))
            carrinho.forEach { item -> root.addView(carrinhoItemCard(item)) }
            root.addView(card("Total geral", formatCurrency(totalCarrinho()), "Adicionar mais itens") { showMontarCarrinho(produtosCache) })
            root.addView(formSection("Ações rápidas", "⚡",
                button("Compartilhar pedido PDF / WhatsApp") { observacaoPedido = obsInput.text.toString(); compartilharPedidoAtual() },
                secondaryButton(if (assinaturaClienteRegistrada) "Assinatura registrada" else "Coletar assinatura do cliente") { observacaoPedido = obsInput.text.toString(); showAssinaturaCliente() }
            ))
            val row = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
            row.addView(budgetButton("Manter como orçamento") {
                observacaoPedido = obsInput.text.toString()
                gerarPedidoLocal("ORCAMENTO")
            }, LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, 0, 0, 10) })
            row.addView(successButton("Enviar pedido") {
                observacaoPedido = obsInput.text.toString()
                gerarPedidoLocal("APROVACAO")
            })
            root.addView(row)
        }
        root.addView(secondaryButton("Cancelar pedido") { carrinho.clear(); clienteSelecionado = null; transportadoraSelecionada = null; condicaoPagamentoSelecionada = null; observacaoPedido = ""; showHome() })
    }

    private fun carrinhoItemCard(item: CarrinhoItem): View {
        val subtotal = subtotalItem(item)
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.WHITE)
            setPadding(28, 22, 28, 22)
            layoutParams = LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, 0, 0, 18) }
        }
        box.addView(TextView(this).apply { text = item.produto.nome; textSize = 18f; typeface = Typeface.DEFAULT_BOLD; setTextColor(azulEscuro) })
        val subtotalBruto = parseCurrency(item.produto.preco) * item.quantidade
        val descontoValor = subtotalBruto - subtotal
        val detalheDesconto = if (item.descontoPercentual > 0.0) " • Desc: ${formatPercent(item.descontoPercentual)} (-${formatCurrency(descontoValor)})" else ""
        box.addView(TextView(this).apply { text = "Qtd: ${item.quantidade} • Unitário ${item.produto.preco}$detalheDesconto • Subtotal ${formatCurrency(subtotal)}"; textSize = 14f; setTextColor(cinzaTexto); setPadding(0,6,0,10) })
        val row = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        row.addView(secondaryButton("-1") { if (item.quantidade > 1) item.quantidade -= 1 else carrinho.remove(item); showCarrinho() }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(0,0,6,0) })
        row.addView(button("+1") { item.quantidade += 1; showCarrinho() }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(6,0,0,0) })
        box.addView(row)
        return box
    }

    private fun gerarPedidoLocal(tipoFinalizacao: String = "ORCAMENTO") {
        val cliente = clienteSelecionado
        if (cliente == null || transportadoraSelecionada == null || condicaoPagamentoSelecionada == null || carrinho.isEmpty()) {
            Toast.makeText(this, "Selecione cliente, transportadora, pagamento e produtos", Toast.LENGTH_LONG).show()
            return
        }

        val envio = PedidoEnvio(
            empresaId = empresaIdAtiva(),
            empresaNome = empresaAtiva?.nome ?: "",
            codigoCliente = cliente.codigo,
            nomeCliente = cliente.nome,
            codigoTransportadora = transportadoraSelecionada?.codigo ?: "",
            nomeTransportadora = transportadoraSelecionada?.nome ?: "",
            codigoCondicaoPagamento = condicaoPagamentoSelecionada?.codigo ?: "",
            condicaoPagamento = condicaoPagamentoSelecionada?.descricao ?: "",
            observacao = observacaoPedido,
            itens = carrinho.map { item ->
                PedidoEnvioItem(
                    codigoProduto = item.produto.codigo,
                    nomeProduto = item.produto.nome,
                    quantidade = item.quantidade,
                    precoUnitario = item.produto.preco,
                    descontoPercentual = item.descontoPercentual,
                    subtotalComDesconto = formatCurrency(subtotalItem(item))
                )
            },
            total = formatCurrency(totalCarrinho()),
            tipoFinalizacao = tipoFinalizacao
        )

        val textoEnvio = if (tipoFinalizacao == "APROVACAO") "Enviando para aprovação..." else "Salvando orçamento..."
        showLoading(if (AppConfig.MOCK_MODE) textoEnvio else "$textoEnvio no ERP Web...")
        Thread {
            val token = usuarioLogado?.token ?: ""
            val result = MobileRepository.criarPedido(token, envio)
            if (result.ok && result.data != null) {
                // V41: se o ERP retornou HTTP 2xx com número/id do pedido, consideramos integrado.
                // A listagem pode demorar ou estar filtrada por empresa/vendedor; por isso não bloqueamos mais
                // o sucesso apenas porque o GET /pedidos não encontrou o pedido imediatamente.
                val atualizacao = if (AppConfig.MOCK_MODE) ApiResult(true, listOf(result.data)) else MobileRepository.pedidos(token, envio.empresaId)
                if (atualizacao.ok && atualizacao.data != null) {
                    mesclarPedidosRemotos(atualizacao.data)
                    salvarCacheOffline()
                }
                runOnUiThread {
                    pedidosCriados.removeAll { it.numero == result.data.numero }
                    pedidosCriados.add(0, result.data)
                    carrinho.clear()
                    clienteSelecionado = null
                    transportadoraSelecionada = null
                    condicaoPagamentoSelecionada = null
                    observacaoPedido = ""
                    val msg = if (tipoFinalizacao == "APROVACAO") "Pedido ${result.data.numero} enviado para aprovação no ERP" else "Orçamento ${result.data.numero} salvo no ERP"
                    Toast.makeText(this, msg, Toast.LENGTH_LONG).show()
                    showPedidoCriado(result.data)
                }
            } else {
                runOnUiThread {
                    pedidosPendentesSync.add(envio)
                    Toast.makeText(this, "Não confirmou no ERP. Pedido salvo offline para sincronizar depois. ${result.message}", Toast.LENGTH_LONG).show()
                    showSincronizacaoOffline()
                }
            }
        }.start()
    }

    private fun showPedidoCriado(p: PedidoResumo) {
        root = baseRoot(); setScreen(root)
        root.addView(topBackBar("Pedido finalizado") { showHome() })
        root.addView(title("Pedido finalizado"))
        root.addView(pedidoCard(p))
        root.addView(successButton("Compartilhar PDF / WhatsApp") { compartilharPedidoResumo(p) })
        root.addView(button("Pedidos") { loadPedidos() })
        root.addView(secondaryButton("Voltar ao painel") { showHome() })
    }

    private fun mesclarPedidosRemotos(remotos: List<PedidoResumo>) {
        remotos.asReversed().forEach { remoto ->
            pedidosCriados.removeAll { it.numero == remoto.numero }
            pedidosCriados.add(0, remoto)
        }
    }

    private fun salvarCacheOffline() {
        getSharedPreferences("vendas2026_config", MODE_PRIVATE)
            .edit()
            .putInt("pedidos_cache_total", pedidosCriados.size)
            .putString("ultima_sincronizacao_info", ultimaSincronizacaoInfo)
            .apply()
    }

    private fun loadPedidos() {
        showLoading("Carregando pedidos...")
        Thread {
            val result = MobileRepository.pedidos(usuarioLogado?.token ?: "", empresaIdAtiva())
            runOnUiThread { if (result.ok && result.data != null) showPedidos(pedidosCriados + result.data) else showError(result.message, ::showHome) }
        }.start()
    }

    private fun showPedidos(pedidos: List<PedidoResumo>) {
        root = baseRoot(); setScreen(root)
        root.addView(topBackBar("Pedidos") { showHome() })
        root.addView(title("Pedidos"))
        root.addView(formSection("Resumo da carteira", "📊",
            twoColumns(miniInfo("Pedidos", pedidos.size.toString(), true), miniInfo("Editáveis", pedidos.count { it.podeEditar }.toString(), true)),
            twoColumns(miniInfo("Integrados", pedidos.count { !it.podeEditar }.toString()), miniInfo("Total local", pedidosCriados.size.toString()))
        ))
        root.addView(premiumSearchBox("Buscar por número, cliente ou status", { q ->
            val filtrados = if (q.isBlank()) pedidosCriados + pedidos else pedidos.filter { it.numero.contains(q, true) || it.cliente.contains(q, true) || it.status.contains(q, true) }
            showPedidos(filtrados)
        }, { loadPedidos() }))
        root.addView(sectionLabel("Pedidos recentes"))
        if (pedidos.isEmpty()) {
            root.addView(card("Nenhum pedido encontrado", "", "Novo pedido") { iniciarNovoPedido() })
        } else {
            pedidos.forEach { p -> root.addView(pedidoCard(p)) }
            root.addView(button("Novo pedido") { iniciarNovoPedido() })
        }
        root.addView(secondaryButton("Voltar ao menu") { showHome() })
    }

    private fun pedidoCard(p: PedidoResumo): View {
        val podeEditar = p.podeEditar
        val corStatus = statusColor(p.status)
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            background = roundedBg(Color.WHITE, 32f, bordaWeb)
            setPadding(22, 18, 22, 18)
            layoutParams = LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, 0, 0, 18) }
        }
        val topo = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
        topo.addView(TextView(this).apply {
            text = "🧾"
            textSize = 28f
            gravity = Gravity.CENTER
            background = roundedBg(azulSoft, 24f, Color.rgb(191, 219, 254))
            setPadding(16, 10, 16, 10)
        })
        topo.addView(LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(16, 0, 0, 0)
            addView(TextView(context).apply { text = "Pedido ${p.numero}"; textSize = 19f; typeface = Typeface.DEFAULT_BOLD; setTextColor(azulEscuro) })
            addView(TextView(context).apply { text = p.cliente; textSize = 14f; setTextColor(cinzaTexto) })
        }, LinearLayout.LayoutParams(0, -2, 1f))
        topo.addView(statusBadge(p.status, corStatus))
        box.addView(topo)
        box.addView(twoColumns(
            miniInfo("Total", p.total, true),
            miniInfo("Edição", if (podeEditar) "Liberada" else "Bloqueada")
        ))
        box.addView(TextView(this).apply {
            text = if (podeEditar) "Editável" else "Integrado"
            textSize = 13f
            setTextColor(if (podeEditar) azul else vermelho)
            setPadding(2, 8, 2, 12)
        })
        box.addView(button(if (podeEditar) "Abrir / reabrir pedido" else "Consultar pedido") {
            Toast.makeText(this, if (podeEditar) "Edição real entra na próxima etapa" else "Pedido bloqueado por integração", Toast.LENGTH_LONG).show()
        })
        return box
    }

    private fun loadProdutos() {
        showLoading("Carregando produtos...")
        Thread {
            val result = MobileRepository.produtos(usuarioLogado?.token ?: "", empresaIdAtiva())
            runOnUiThread { if (result.ok && result.data != null) { produtosCache = result.data; showProdutos(result.data) } else showError(result.message, ::showHome) }
        }.start()
    }

    private fun showProdutos(produtos: List<ProdutoResumo>) {
        root = baseRoot(); setScreen(root)
        root.addView(topBackBar("Produtos") { showHome() })
        root.addView(title("Produtos"))
        root.addView(subtitle("Consulta de catálogo com foto, categoria, preço, estoque e detalhes comerciais."))

        val busca = EditText(this).apply { hint = "Buscar por código, nome ou categoria"; setSingleLine(true) }
        root.addView(busca)

        val rowBusca = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        rowBusca.addView(button("Buscar") {
            val q = busca.text.toString().trim()
            showProdutos(if (q.isBlank()) produtosCache else produtosCache.filter {
                it.codigo.contains(q, true) || it.nome.contains(q, true) || it.categoria.contains(q, true)
            })
        }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(0,0,8,0) })
        rowBusca.addView(secondaryButton("Limpar") { showProdutos(produtosCache) }, LinearLayout.LayoutParams(0, -2, 1f).apply { setMargins(8,0,0,0) })
        root.addView(rowBusca)

        root.addView(sectionLabel("Catálogo"))
        if (produtos.isEmpty()) {
            root.addView(card("Nenhum produto encontrado", "", "Voltar ao catálogo") { showProdutos(produtosCache) })
        } else {
            produtos.forEach { p -> root.addView(produtoConsultaCard(p)) }
        }
        root.addView(secondaryButton("Voltar") { showHome() })
    }

    private fun produtoConsultaCard(p: ProdutoResumo): View {
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.WHITE)
            setPadding(28, 22, 28, 22)
            layoutParams = LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, 0, 0, 18) }
        }
        box.addView(produtoImage(p, 260))
        box.addView(TextView(this).apply {
            text = "${p.codigo} - ${p.nome}"
            textSize = 19f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(azulEscuro)
            setPadding(0, 14, 0, 4)
        })
        box.addView(TextView(this).apply {
            text = "${p.categoria} • ${p.preco} • Estoque: ${p.estoque}"
            textSize = 14f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(if (p.estoque > 0) cinzaTexto else vermelho)
            setPadding(0, 0, 0, 10)
        })
        box.addView(TextView(this).apply {
            text = p.descricao
            textSize = 14f
            setTextColor(cinzaTexto)
            setPadding(0, 0, 0, 12)
        })
        box.addView(button("Consultar detalhes") { showProdutoDetalhe(p) })
        return box
    }

    private fun showProdutoDetalhe(p: ProdutoResumo) {
        root = baseRoot(); setScreen(root)
        root.addView(title(p.nome))
        root.addView(produtoImage(p, 420))
        root.addView(card("Código", p.codigo, "Copiar código") {
            Toast.makeText(this, "Código ${p.codigo}", Toast.LENGTH_SHORT).show()
        })
        root.addView(card("Informações comerciais", "Categoria: ${p.categoria}\nPreço tabela: ${p.preco}\nEstoque disponível: ${p.estoque}", "Adicionar em novo pedido") {
            if (produtosCache.isEmpty()) produtosCache = MockRepository.produtos(empresaIdAtiva())
            iniciarNovoPedido()
        })
        root.addView(card("Descrição", p.descricao, "Voltar ao catálogo") { showProdutos(produtosCache) })
        root.addView(secondaryButton("Voltar para produtos") { showProdutos(produtosCache) })
    }

    private fun produtoImage(p: ProdutoResumo, altura: Int): ImageView = ImageView(this).apply {
        val resId = resources.getIdentifier(p.fotoRes, "drawable", packageName)
        if (resId != 0) setImageResource(resId) else setImageResource(resources.getIdentifier("produto_padrao", "drawable", packageName))
        scaleType = ImageView.ScaleType.CENTER_CROP
        adjustViewBounds = true
        setBackgroundColor(bordaWeb)
        layoutParams = LinearLayout.LayoutParams(-1, altura).apply { setMargins(0, 0, 0, 8) }
    }

    private fun showConfig() {
        root = baseRoot(); setScreen(root)
        root.addView(topBackBar("Configurar servidor") { showLogin() })
        root.addView(title("Conectar ao ERP"))
        root.addView(subtitle("Use a URL online do ERP publicado no Render."))

        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            background = roundedBg(Color.WHITE, 34f, bordaWeb)
            setPadding(24, 22, 24, 24)
            layoutParams = LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, 0, 0, 16) }
        }
        val urlInput = premiumInput("Servidor", AppConfig.API_BASE_URL)
        urlInput.setText(AppConfig.API_BASE_URL)
        box.addView(TextView(this).apply { text = "Cole aqui a URL do ERP no Render, sem barra no final."; textSize = 13f; setTextColor(cinzaTexto); setPadding(0,0,0,12) })
        box.addView(labeledField("Endereço do servidor", urlInput))
        box.addView(TextView(this).apply {
            text = "Exemplo:\nhttps://vendas2026-erp.onrender.com"
            textSize = 13f
            setTextColor(cinzaTexto)
            setPadding(0, 4, 0, 14)
        })
        box.addView(button("Salvar servidor") {
            saveApiConfig(urlInput.text.toString())
            Toast.makeText(this, "Servidor salvo: ${AppConfig.API_BASE_URL}", Toast.LENGTH_LONG).show()
            showLogin()
        })
        box.addView(secondaryButton("Testar conexão") {
            testApiConnection(normalizeApiUrl(urlInput.text.toString()))
        }, LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, dp(10), 0, 0) })
        root.addView(box)

        root.addView(card("Endereço atual", AppConfig.API_BASE_URL, "Voltar") { showLogin() })
    }

    private fun testApiConnection(baseUrl: String) {
        showLoading("Testando conexão...")
        Thread {
            try {
                val conn = (URL(baseUrl.trimEnd('/') + "/api/mobile/ping").openConnection() as HttpURLConnection).apply {
                    requestMethod = "GET"
                    connectTimeout = 7000
                    readTimeout = 7000
                    setRequestProperty("Accept", "application/json")
                }
                val ok = conn.responseCode in 200..299
                runOnUiThread {
                    Toast.makeText(this, if (ok) "Conexão OK" else "Servidor respondeu HTTP ${conn.responseCode}", Toast.LENGTH_LONG).show()
                    if (ok) saveApiConfig(baseUrl)
                    showConfig()
                }
            } catch (e: Exception) {
                runOnUiThread {
                    Toast.makeText(this, e.message ?: "Falha ao conectar", Toast.LENGTH_LONG).show()
                    showConfig()
                }
            }
        }.start()
    }


    private fun showSincronizacaoOffline() {
        root = baseRoot(); setScreen(root)
        root.addView(topBackBar("Offline") { showHome() })
        root.addView(title("Offline e sincronização"))
        root.addView(subtitle("Envie pedidos pendentes, receba dados do ERP e aplique configurações remotas do app."))
        root.addView(formSection("Status", "🔄",
            twoColumns(kpi("${pedidosPendentesSync.size}", "Pendentes"), kpi("ERP", "Online")),
            TextView(this).apply {
                text = ultimaSincronizacaoInfo
                textSize = 13.5f
                setTextColor(cinzaTexto)
                setPadding(0, 8, 0, 0)
            }
        ))
        if (pedidosPendentesSync.isNotEmpty()) {
            root.addView(sectionLabel("Pedidos aguardando envio"))
            pedidosPendentesSync.forEachIndexed { index, pedido ->
                root.addView(card("Pendente #${index + 1}", "${pedido.nomeCliente} • ${pedido.total} • ${pedido.itens.size} itens", "Compartilhar") { compartilharTexto(montarTextoPedido(pedido)) })
            }
        } else {
            root.addView(infoBox("Tudo sincronizado neste aparelho. Você ainda pode tocar em sincronizar para receber status, produtos, clientes, transportadoras e condições atualizadas do ERP."))
        }
        root.addView(successButton("Sincronizar agora") { sincronizarTudoComErp() })
        root.addView(secondaryButton("Voltar") { showHome() }, LinearLayout.LayoutParams(-1, -2).apply { setMargins(0, dp(10), 0, 0) })
    }

    private fun sincronizarTudoComErp() {
        showLoading("Sincronizando com o ERP...")
        Thread {
            val token = usuarioLogado?.token ?: ""
            val empresaId = empresaIdAtiva()
            val enviados = mutableListOf<PedidoEnvio>()
            var atualizacoesRecebidas = 0
            var erros = 0

            pedidosPendentesSync.toList().forEach { pedido ->
                val result = MobileRepository.criarPedido(token, pedido)
                if (result.ok) enviados.add(pedido) else erros++
            }

            val pedidosResult = MobileRepository.pedidos(token, empresaId)
            if (pedidosResult.ok && pedidosResult.data != null) {
                atualizacoesRecebidas += pedidosResult.data.size
            } else erros++

            val produtosResult = MobileRepository.produtos(token, empresaId)
            if (produtosResult.ok && produtosResult.data != null) {
                produtosCache = produtosResult.data
                atualizacoesRecebidas += produtosResult.data.size
            } else erros++

            val clientesResult = MobileRepository.clientes(token)
            if (clientesResult.ok && clientesResult.data != null) {
                clientesCache = clientesCriados + clientesResult.data
                atualizacoesRecebidas += clientesResult.data.size
            } else erros++

            val transportadorasResult = MobileRepository.transportadoras(token)
            if (transportadorasResult.ok && transportadorasResult.data != null) {
                transportadorasCache = transportadorasCriadas + transportadorasResult.data
                atualizacoesRecebidas += transportadorasResult.data.size
            } else erros++

            val condicoesResult = MobileRepository.condicoesPagamento(token)
            if (condicoesResult.ok && condicoesResult.data != null) {
                condicoesPagamentoCache = condicoesResult.data
                atualizacoesRecebidas += condicoesResult.data.size
            } else erros++

            var configRecebida = false
            val configResult = MobileRepository.mobileConfig(token)
            if (configResult.ok && configResult.data != null) {
                remoteConfig = configResult.data
                configRecebida = true
            }

            runOnUiThread {
                pedidosPendentesSync.removeAll(enviados)
                ultimaSincronizacaoInfo = "Enviados: ${enviados.size} • Atualizações: $atualizacoesRecebidas" + (if (configRecebida) " • Configuração aplicada" else "") + (if (erros > 0) " • Pendências: $erros" else " • Tudo certo")
                Toast.makeText(this, ultimaSincronizacaoInfo, Toast.LENGTH_LONG).show()
                showSincronizacaoOffline()
            }
        }.start()
    }

    private fun sincronizarPendentes() {
        sincronizarTudoComErp()
    }

    private fun montarPedidoAtual(): PedidoEnvio? {
        val cliente = clienteSelecionado ?: return null
        return PedidoEnvio(
            empresaId = empresaIdAtiva(),
            empresaNome = empresaAtiva?.nome ?: "",
            codigoCliente = cliente.codigo,
            nomeCliente = cliente.nome,
            codigoTransportadora = transportadoraSelecionada?.codigo ?: "",
            nomeTransportadora = transportadoraSelecionada?.nome ?: "",
            codigoCondicaoPagamento = condicaoPagamentoSelecionada?.codigo ?: "",
            condicaoPagamento = condicaoPagamentoSelecionada?.descricao ?: "",
            observacao = observacaoPedido,
            itens = carrinho.map { item -> PedidoEnvioItem(item.produto.codigo, item.produto.nome, item.quantidade, item.produto.preco, item.descontoPercentual, formatCurrency(subtotalItem(item))) },
            total = formatCurrency(totalCarrinho()),
            tipoFinalizacao = "ORCAMENTO"
        )
    }

    private fun montarTextoPedido(p: PedidoEnvio): String {
        val itensTexto = p.itens.joinToString("\n") { "• ${it.nomeProduto} | Qtd ${it.quantidade} | Desc. ${formatPercent(it.descontoPercentual)} | ${it.subtotalComDesconto}" }
        val assinatura = if (assinaturaClienteRegistrada) "\nAssinatura do cliente: registrada no app" else ""
        return "Pedido Vendas 2026\nEmpresa: ${p.empresaNome}\nCliente: ${p.nomeCliente}\nTransportadora: ${p.nomeTransportadora}\nPagamento: ${p.condicaoPagamento}\n\nItens:\n$itensTexto\n\nTotal: ${p.total}\nObservação: ${p.observacao}$assinatura"
    }

    private fun montarTextoPedidoResumo(p: PedidoResumo): String {
        return "Pedido Vendas 2026\nNúmero: ${p.numero}\nCliente: ${p.cliente}\nStatus: ${p.status}\nTotal: ${p.total}\nEmpresa: ${empresaAtiva?.nome ?: ""}"
    }

    private fun compartilharPedidoAtual() {
        val pedido = montarPedidoAtual()
        if (pedido == null || carrinho.isEmpty()) {
            Toast.makeText(this, "Monte o pedido antes de compartilhar", Toast.LENGTH_LONG).show()
            return
        }
        compartilharTexto(montarTextoPedido(pedido))
        gerarPdfPedido(montarTextoPedido(pedido))
    }

    private fun compartilharPedidoResumo(p: PedidoResumo) {
        val texto = montarTextoPedidoResumo(p)
        compartilharTexto(texto)
        gerarPdfPedido(texto)
    }

    private fun compartilharTexto(texto: String) {
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "text/plain"
            putExtra(Intent.EXTRA_TEXT, texto)
        }
        startActivity(Intent.createChooser(intent, "Compartilhar pedido"))
    }

    private fun gerarPdfPedido(texto: String) {
        try {
            val pdf = PdfDocument()
            val pageInfo = PdfDocument.PageInfo.Builder(595, 842, 1).create()
            val page = pdf.startPage(pageInfo)
            val paint = Paint().apply { color = Color.BLACK; textSize = 14f }
            var y = 42f
            texto.split("\n").forEach { linha ->
                page.canvas.drawText(linha.take(78), 32f, y, paint)
                y += 22f
                if (y > 800f) y = 800f
            }
            pdf.finishPage(page)
            val file = File(cacheDir, "pedido_vendas2026.pdf")
            file.outputStream().use { pdf.writeTo(it) }
            pdf.close()
            try { android.os.StrictMode::class.java.getMethod("disableDeathOnFileUriExposure").invoke(null) } catch (_: Exception) {}
            val intent = Intent(Intent.ACTION_SEND).apply {
                type = "application/pdf"
                putExtra(Intent.EXTRA_STREAM, Uri.fromFile(file))
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            startActivity(Intent.createChooser(intent, "Enviar PDF do pedido"))
        } catch (e: Exception) {
            Toast.makeText(this, "Texto do pedido compartilhado. PDF não pôde ser gerado: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    private fun showAssinaturaCliente() {
        root = baseRoot(); setScreen(root)
        root.addView(topBackBar("Assinatura") { showCarrinho() })
        root.addView(title("Assinatura do cliente"))
        root.addView(subtitle("Peça para o cliente assinar no quadro abaixo."))
        val signature = SignatureView(this)
        root.addView(signature, LinearLayout.LayoutParams(-1, dp(260)).apply { setMargins(0, 0, 0, 18) })
        root.addView(successButton("Salvar assinatura") {
            assinaturaClienteRegistrada = true
            Toast.makeText(this, "Assinatura registrada no pedido", Toast.LENGTH_LONG).show()
            showCarrinho()
        })
        root.addView(secondaryButton("Limpar assinatura") { signature.clear() })
        root.addView(secondaryButton("Voltar") { showCarrinho() })
    }

    inner class SignatureView(context: android.content.Context) : View(context) {
        private val path = Path()
        private val paint = Paint().apply {
            color = azulEscuro
            strokeWidth = 5f
            style = Paint.Style.STROKE
            isAntiAlias = true
        }
        init { background = roundedBg(Color.WHITE, 28f, Color.rgb(203, 213, 225)) }
        override fun onDraw(canvas: Canvas) { super.onDraw(canvas); canvas.drawPath(path, paint) }
        override fun onTouchEvent(event: android.view.MotionEvent): Boolean {
            when (event.action) {
                android.view.MotionEvent.ACTION_DOWN -> path.moveTo(event.x, event.y)
                android.view.MotionEvent.ACTION_MOVE -> path.lineTo(event.x, event.y)
            }
            invalidate()
            return true
        }
        fun clear() { path.reset(); invalidate(); assinaturaClienteRegistrada = false }
    }

    private fun showError(msg: String, back: () -> Unit) {
        root = baseRoot(); setScreen(root)
        root.addView(title("Não foi possível carregar"))
        root.addView(subtitle(msg.ifBlank { "Verifique a URL da API ou ative o modo mock." }))
        root.addView(secondaryButton("Voltar") { back() })
    }

    private fun statusColor(status: String): Int = when {
        status.contains("integrado", true) -> verde
        status.contains("aprovado", true) -> azul
        status.contains("orçamento", true) -> amarelo
        status.contains("digitação", true) -> cinzaTexto
        else -> cinzaTexto
    }

    private fun parseCurrency(value: String): Double {
        return value.replace("R$", "").replace(".", "").replace(",", ".").trim().toDoubleOrNull() ?: 0.0
    }

    private fun subtotalItem(item: CarrinhoItem): Double = parseCurrency(item.produto.preco) * item.quantidade * (1 - item.descontoPercentual / 100.0)

    private fun totalCarrinho(): Double = carrinho.sumOf { subtotalItem(it) }

    private fun formatPercent(value: Double): String = String.format(Locale("pt", "BR"), "%.2f%%", value).replace(",00%", "%")

    private fun formatCurrency(value: Double): String = NumberFormat.getCurrencyInstance(Locale("pt", "BR")).format(value)
}
