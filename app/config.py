import os

class Config:
    """
    Classe de configuração centralizada.
    Armazena constantes, chaves de API e mapeamentos de diretórios.
    """
    
    # Chave secreta para assinatura de sessões
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    
    # Configurações de Upload
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024 * 1024 
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'session_data')

    # Mapeamento de Escolas para IDs de Pastas do Google Drive
    FOLDER_MAP = {
        "ASSOCIAÇÃO JOÃO PAULO II": "1kLMegBUcgY3rm6FhQqs3ef_qPBGTkUUJ",
        "CAIC - PROF FEBRONIO TANCREDO DE OLIVEIRA": "1-UkASIHmSbHcATaFz7JFgUnucqDQyftR",
        "CEI AMIGUINHOS DA COMUNIDADE": "1pKY_cygs9W_nrvRrOgUMzwE9JJqMzvOH",
        "CEI ANJINHO DA GUARDA": "1MGAq4JuCquC2A3Yifz3_YxUbTm1L-CS6",
        "CEI APRENDER BRINCANDO": "1-6s1gKbXqc3CgOzwPcAe5i_yzqmDR87T",
        "CEI AQUARELA": "19k0bi0BGE1PEZq9vMPIY_VJxUcmFZyH_",
        "CEI BOLINHAS DE SABÃO": "1YMhRIttlEQ_utujSMB3SACUuYH7UGtCF",
        "CEI CAIC": "1349mhOOgyjUGiToktK4oUYhIBsy70CyK",
        "CEI CAMINHO DO APRENDER": "1a6Yru89FI2xEuGv6AhOnSeU6wiUSVtGY",
        "CEI CAMINHO DA IMAGINAÇÃO": "1iR-wPH8a6hhV5f5A8CHlkPtBOMgbXyhB",
        "CEI CANARINHO": "1c3u-oHV2OwDz_MWBIvnADGHYsME-k3uO",
        "CEI CHAPEUZINHO VERMELHO": "1V_98E-zCEtGgD3VkvNQks8mu_FTZcohP",
        "CEI CIRANDA COLORIDA": "19-fXxBvReRZBeStMnD9FoSjC5G281gMY",
        "CEI CONVIVER": "1-LD-2ZM2WYcdf5XvAJ-hEVIXoE0c2x4p",
        "CEI CRIANÇA FELIZ": "1EBY4W18yRPeoFhVtnkfoeaTgIXh6E-9-",
        "CEI DONA MARICOTA": "1Ug1klBR12QnPtsGHqHs21Bd9ZTb15MVX",
        "CEI ESPAÇO CRIATIVO": "1UcXHBDnkepLmoFQuV8WvnlWEfFfIG5gW",
        "CEI ESTRELA DO MAR PROF REGINA CAETANA DA SILVEIRA": "1BgTYM6-zqaotJi3Prv6brqowEkAOntX4",
        "CEI ESTRELINHA": "1p2ynK1R0rPaRdeSVG5X1mFJ5z3QYKNWQ",
        "CEI FLORZINHA AZUL": "1rc0IOpETOf_XYMbI2TBoASc4WOXcRtD5",
        "CEI FORMIGUINHAS": "1t6C7jBhlM_zf1W_oJPTjSC_IhQtyjfPI",
        "CEI FILHOS DA TERRA": "1Lhb_BW32fqTsb0GMJFtmqE3iMHitS9FE",
        "CEI INOVAÇÃO": "1jp6TDLZQdGZoohCGI3iqFCM3LlKStOyg",
        "CEI INTERAÇÃO": "17BfjF141b83WBdEQJvq2-VQn9JT5FGFg",
        "CEI JOSÉ MIGUEL FERREIRA": "1pp1CKwAT2JRi1sCKtFVp5XVgZQU6RvXo",
        "CEI MUNDO ENCANTADO": "1mrMz_0DieVuzWY-9bN92NLN_1EOCKzML",
        "CEI MUNDO MÁGICO": "1IGBHHgP7JX_12U_3K2eaqp1R3JoFpQQl",
        "CEI MARIA DOS SANTOS SILVA": "1J5pPh3DeWH2K4sM1ZMN3a4HVvgXq_XoJ",
        "CEI MARIA JOSÉ DE MEDEIROS": "1B4SgduPr9G57ezVEGAnbYO3qFxyzfrke",
        "CEI NOVA ESPERANÇA": "1MvpzjV9qqJW4LXE_7KuSjMCjap3SxNvb",
        "CEI NOVA GERAÇÃO": "19CYQOiyiniNxyaod_eXGQgsbNOdX4Gm0",
        "CEI PADRE RÉUS": "1lFeSgBp3St9YfGbeG6zPAqZgy3Jhr_FI",
        "CEI PARAÍSO": "1Vqir9zdi-d3vWeRgpodYTh1OXX5QnyHW",
        "CEI PARAÍSO DO AMOR": "1il6x2Xm2wVNvTNC66Mo52f2IWpW7DHA-",
        "CEI PRIMEIROS PASSOS": "1bRQ5VBKA8zJXvVQo4EmjUWGEgaY6KepJ",
        "CEI PROF ARGEMIRA DE FARIAS DA SILVEIRA": "1aDbRoaBWrMlrkwnwTkYVP139w-fHDaeu",
        "CEI PROF AURORA DA SILVA LOPES": "1LJvGgjxVnEnhcF-I8Gw3YWtpYL_9X3F-",
        "CEI PROF INÊS MARTA DA SILVA": "1ccfZ8c2mFDppoMNUSMvDS-vB6Qtr3_C1",
        "CEI PROF PAULO BRAULIO GOULART": "1w-XFwNjqfKnnyjLPC5LleJiY7dtExxBV",
        "CEI REALIZAR": "1QlMfcJvuBL_mk_nJnwLZPYqdlirzfzS9",
        "CEI RODA VIVA": "1fgAwmpxUYtlCDfX1nzzEKPFS6iyF_L01",
        "CEI ROMEU E JULIETA": "1-c4ukU7sm2r0H0OXc_GYwyE5Gq7ia1HH",
        "CEI SANTA MARTA": "1SznKiYRoU5U-grlb6O4HGpyTbq76Uh3q",
        "CEI SÃO TOMÉ": "1mQy9VMbAcjHGOQzVdL_41ub0LsfJeqSn",
        "CEI SNOOPY": "1_HE3SKhoobvjMX1KBW38a_7pxPlnsYK8",
        "CEI ULISSES GUIMARÃES": "12-4dOO34kt1cmd3aRSqS1u3aFDpkfhaS",
        "CEI VALE VERDE PROF. MAURICIO SCHMITT": "1m24vkdQA5OfC8oFAgUpI0S3-VVoD1R28",
        "CEI VIDA MELHOR": "1LHYT4RoP-GpMH-SlrmnO7ZcEHZomc5pq",
        "CEI VÓ LAURA": "1iAgYBbCdAEejcdeQbtpIT7f4-HL-WXfP",
        "CEI VOO LIVRE": "11pNNnZv-rt3rtuMKPRmofV0aiXeiyGLP",
        "CEI VOVÓ MARIA": "1swvqoYYpvLohJLSYG7JHNTNTSNOdsfIu",
        "CEI VOVÓ DOLORES": "1AIqUosA0aoHAj70ZSAlD2Zbv5ooorwlM",
        "EB ABÍLIO MANOEL DE ABREU": "1glRdVOvRaG1op6JwRucCX0mOddgROUNo",
        "EB ANTONIETA SILVEIRA DE SOUZA": "1WD7eIwcYYhuSyBHwTC_dWzt5SYbKHlW8",
        "EB FREI DAMIÃO": "1d0qZQ_21YgorpcfZkWVsgdU7KTGsyLPw",
        "EB NERI BRASILIANO MARTINS": "1EFcd5ex43IS3fmsn5_pfp_wHf6OXuiS_",
        "EB NOSSA SENHORA DE FÁTIMA": "1400C0SwQyQOdxL3QA2a64QHFmfHc6bx3",
        "EB PROF FRANCISCA RAIMUNDA FARIAS DA COSTA": "1QCu3JKA-j9NcNx1S3u7YmtE-rvGULoiz",
        "EB PROF LAURITA WAGNER DA SILVEIRA": "1WaH0bRN8uchnfeJ5b3jKS4wdQ8JIHeZQ",
        "EB PROFª ADRIANA WEINGARTNER": "1GWEreDqadg_Zl-SmqhAZcFvWCeUc5Hj8",
        "EB VIVIANE LAURITA DE QUADROS COELHO": "1t6pfkPCt9e-FWFm8-7Dqh__m96TVj6El",
        "EBM PROF MARA LUIZA VIEIRA LIBERATO": "183cvM1qEpV71_dnx3w03bQsxyinExRxO",
        "EBM PROF. OSMAR ANTÔNIO VIEIRA": "1kyFKSlHhbgioK4UVS2D1andUIFZU7CGr",
        "EBM REINALDO WEINGARTNER": "17BpeoPxLdJ5qx4kNKXyQbZcrirY0X4ZN",
        "EI DO RINCÃO": "1Pi3mvEVCfDvWRAZMBG5xhIY9RIBs9B-G",
        "ER ALBARDÃO": "1Jx_0jYqqNA_wRt1bi0Z0z6WAT2wN3zng",
        "ER BENTO JOSÉ DO NASCIMENTO": "10jFESDgl1HdBCKmUx1G5wZXLwIlNbHNp",
        "ER DANIEL CARLOS WEINGARTNER": "140R2R8dhGhulUk5i_bcjl1jDv_4CASAn",
        "ER ISABEL BOTELHO DE PAULO": "1oVxgcDKvYNiK6J6i5UDcQR0NCiXdWzcG",
        "ER MANOEL DA SILVA": "1UHBCjna6htCxwt7Lm9xpawoSLC8hbJyV",
        "ER OLGA CERINO": "1gJsmtEGZiO29mkcPZFmiAzfKnWP7VYft",
        "FUNDAÇÃO FÉ E ALEGRIA DO BRASIL": "115Uedk-xJuxq-_QQfcbyceNjsgnR53qq",
        "FUNDAÇÃO HERMON": "1QnXsjd0j8utnVJKQAzLyavd9Yd3G9RMy",
        "GE EVANDA SUELLI JUTTEL MACHADO": "1vn2dNVJ69EL_336T7EQhSLdDUubkyYXV",
        "GE GUILHERME WIETHORN FILHO": "1csA3VaJhMHlL12JBQMzfZuuoCbCNKD2s",
        "GE NAJLA CARONE GUEDERT": "1Pr-eC4vfs7tflB7ioyl7OBil_ou8Qn9W",
        "GE PEQUENO PRÍNCIPE": "1EDtxQt7pN7Gfm2EbvUvqAEobALiQA2bg",
        "GE PROF MARIA LUZIA DE SOUZA": "1thWDatQxhkVQrNa7PBsazVcn_enU0PvQ",
        "GE TEREZINHA MARIA ESPÍNDOLA MARTINS": "1DWtQi7U1Iat-7co8DywDiZs0aSPbZIRu"
    }