""" Live Test for:
    1) Encoding Request
    2) Logon Request
    3) Market Data Request
    4) and manual function to logoff and close socket
"""
import socket
import struct
import threading
import logging
import DTC_Files.DTCProtocol_pb2 as Dtc
import ssl

# Standar loggers for all functions
logMsg = logging.getLogger('johndtc')
logStdout = logging.getLogger('johnstdout')

logMsg.setLevel(logging.DEBUG)
logStdout.setLevel(logging.DEBUG)

logMsg_handler = logging.FileHandler('log-msgs.txt')
stdout_handler = logging.StreamHandler()

fmtMsg = logging.Formatter("%(asctime)s : %(levelname)s : %(funcName)s : %(message)s")
fmtStdout = logging.Formatter("%(asctime)s : %(levelname)s : %(funcName)s : %(message)s")

logMsg_handler.setFormatter(fmtMsg)
stdout_handler.setFormatter(fmtStdout)

logMsg.addHandler(logMsg_handler)
logStdout.addHandler(stdout_handler)

# Mapping message type to DTC message object and human readable name
DTC_MTYPE_MAP = {
 1: ['LOGON_REQUEST', 0, 1, Dtc.LogonRequest],
 2: ['LOGON_RESPONSE', 1, 2, Dtc.LogonResponse],
 3: ['HEARTBEAT', 2, 3, Dtc.Heartbeat],
 5: ['LOGOFF', 3, 5, Dtc.Logoff],
 6: ['ENCODING_REQUEST', 4, 6, Dtc.EncodingRequest],
 7: ['ENCODING_RESPONSE', 5, 7, Dtc.EncodingResponse],
 101: ['MARKET_DATA_REQUEST', 6, 101, Dtc.MarketDataRequest],
 103: ['MARKET_DATA_REJECT', 7, 103, Dtc.MarketDataReject],
 104: ['MARKET_DATA_SNAPSHOT', 8, 104, Dtc.MarketDataSnapshot],
 107: ['MARKET_DATA_UPDATE_TRADE', 10, 107, Dtc.MarketDataUpdateTrade],
 112: ['MARKET_DATA_UPDATE_TRADE_COMPACT', 11, 112, Dtc.MarketDataUpdateTradeCompact],
 134: ['MARKET_DATA_UPDATE_LAST_TRADE_SNAPSHOT', 13, 134, Dtc.MarketDataUpdateLastTradeSnapshot],
 108: ['MARKET_DATA_UPDATE_BID_ASK', 14, 108, Dtc.MarketDataUpdateBidAsk],
 117: ['MARKET_DATA_UPDATE_BID_ASK_COMPACT', 15, 117, Dtc.MarketDataUpdateBidAskCompact],
 120: ['MARKET_DATA_UPDATE_SESSION_OPEN', 17, 120, Dtc.MarketDataUpdateSessionOpen],
 114: ['MARKET_DATA_UPDATE_SESSION_HIGH', 19, 114, Dtc.MarketDataUpdateSessionHigh],
 115: ['MARKET_DATA_UPDATE_SESSION_LOW', 21, 115, Dtc.MarketDataUpdateSessionLow],
 113: ['MARKET_DATA_UPDATE_SESSION_VOLUME', 23, 113, Dtc.MarketDataUpdateSessionVolume],
 124: ['MARKET_DATA_UPDATE_OPEN_INTEREST', 24, 124, Dtc.MarketDataUpdateOpenInterest],
 119: ['MARKET_DATA_UPDATE_SESSION_SETTLEMENT', 25, 119, Dtc.MarketDataUpdateSessionSettlement],
 135: ['MARKET_DATA_UPDATE_SESSION_NUM_TRADES', 27, 135, Dtc.MarketDataUpdateSessionNumTrades],
 136: ['MARKET_DATA_UPDATE_TRADING_SESSION_DATE', 28, 136, Dtc.MarketDataUpdateTradingSessionDate],
 102: ['MARKET_DEPTH_REQUEST', 29, 102, Dtc.MarketDepthRequest],
 121: ['MARKET_DEPTH_REJECT', 30, 121, Dtc.MarketDepthReject],
 122: ['MARKET_DEPTH_SNAPSHOT_LEVEL', 31, 122, Dtc.MarketDepthSnapshotLevel],
 106: ['MARKET_DEPTH_UPDATE_LEVEL', 33, 106, Dtc.MarketDepthUpdateLevel],
 118: ['MARKET_DEPTH_UPDATE_LEVEL_COMPACT', 34, 118, Dtc.MarketDepthUpdateLevelCompact],
 123: ['MARKET_DEPTH_FULL_UPDATE_10', 36, 123, Dtc.MarketDepthFullUpdate10],
 105: ['MARKET_DEPTH_FULL_UPDATE_20', 37, 105, Dtc.MarketDepthFullUpdate20],
 100: ['MARKET_DATA_FEED_STATUS', 38, 100, Dtc.MarketDataFeedStatus],
 116: ['MARKET_DATA_FEED_SYMBOL_STATUS', 39, 116, Dtc.MarketDataFeedSymbolStatus],
 208: ['SUBMIT_NEW_SINGLE_ORDER', 40, 208, Dtc.SubmitNewSingleOrder],
 203: ['CANCEL_ORDER', 44, 203, Dtc.CancelOrder],
 204: ['CANCEL_REPLACE_ORDER', 45, 204, Dtc.CancelReplaceOrder],
 300: ['OPEN_ORDERS_REQUEST', 47, 300, Dtc.OpenOrdersRequest],
 302: ['OPEN_ORDERS_REJECT', 48, 302, Dtc.OpenOrdersReject],
 301: ['ORDER_UPDATE', 49, 301, Dtc.OrderUpdate],
 303: ['HISTORICAL_ORDER_FILLS_REQUEST', 50, 303, Dtc.HistoricalOrderFillsRequest],
 304: ['HISTORICAL_ORDER_FILL_RESPONSE', 51, 304, Dtc.HistoricalOrderFillResponse],
 308: ['HISTORICAL_ORDER_FILLS_REJECT', 52, 308, Dtc.HistoricalOrderFillsReject],
 305: ['CURRENT_POSITIONS_REQUEST', 53, 305, Dtc.CurrentPositionsRequest],
 307: ['CURRENT_POSITIONS_REJECT', 54, 307, Dtc.CurrentPositionsReject],
 306: ['POSITION_UPDATE', 55, 306, Dtc.PositionUpdate],
 400: ['TRADE_ACCOUNTS_REQUEST', 56, 400, Dtc.TradeAccountsRequest],
 401: ['TRADE_ACCOUNT_RESPONSE', 57, 401, Dtc.TradeAccountResponse],
 500: ['EXCHANGE_LIST_REQUEST', 58, 500, Dtc.ExchangeListRequest],
 501: ['EXCHANGE_LIST_RESPONSE', 59, 501, Dtc.ExchangeListResponse],
 502: ['SYMBOLS_FOR_EXCHANGE_REQUEST', 60, 502, Dtc.SymbolsForExchangeRequest],
 503: ['UNDERLYING_SYMBOLS_FOR_EXCHANGE_REQUEST', 61, 503, Dtc.UnderlyingSymbolsForExchangeRequest],
 504: ['SYMBOLS_FOR_UNDERLYING_REQUEST', 62, 504, Dtc.SymbolsForUnderlyingRequest],
 506: ['SECURITY_DEFINITION_FOR_SYMBOL_REQUEST', 63, 506, Dtc.SecurityDefinitionForSymbolRequest],
 507: ['SECURITY_DEFINITION_RESPONSE', 64, 507, Dtc.SecurityDefinitionResponse],
 508: ['SYMBOL_SEARCH_REQUEST', 65, 508, Dtc.SymbolSearchRequest],
 509: ['SECURITY_DEFINITION_REJECT', 66, 509, Dtc.SecurityDefinitionReject],
 601: ['ACCOUNT_BALANCE_REQUEST', 67, 601, Dtc.AccountBalanceRequest],
 602: ['ACCOUNT_BALANCE_REJECT', 68, 602, Dtc.AccountBalanceReject],
 600: ['ACCOUNT_BALANCE_UPDATE', 69, 600, Dtc.AccountBalanceUpdate],
 700: ['USER_MESSAGE', 70, 700, Dtc.UserMessage],
 701: ['GENERAL_LOG_MESSAGE', 71, 701, Dtc.GeneralLogMessage],
 800: ['HISTORICAL_PRICE_DATA_REQUEST', 72, 800, Dtc.HistoricalPriceDataRequest],
 801: ['HISTORICAL_PRICE_DATA_RESPONSE_HEADER', 73, 801, Dtc.HistoricalPriceDataResponseHeader],
 802: ['HISTORICAL_PRICE_DATA_REJECT', 74, 802, Dtc.HistoricalPriceDataReject],
 803: ['HISTORICAL_PRICE_DATA_RECORD_RESPONSE', 75, 803, Dtc.HistoricalPriceDataRecordResponse],
 804: ['HISTORICAL_PRICE_DATA_TICK_RECORD_RESPONSE', 76, 804, Dtc.HistoricalPriceDataTickRecordResponse],
}

TYPE_TO_STRUCT_FORMAT = {
    1: "i",  # CPPTYPE_INT32
    2: "l",  # CPPTYPE_INT64
    3: "I",  # CPPTYPE_UINT32
    4: "L",  # CPPTYPE_UINT64
    5: "d",  # CPPTYPE_DOUBLE
    6: "f",  # CPPTYPE_FLOAT
    7: "?",  # CPPTYPE_BOOL
    8: "ENUM",  # CPPTYPE_ENUM; Special handling required
    9: "s",  # CPPTYPE_STRING
    10: "s"  # CPPTYPE_MESSAGE; TODO: this is an assumption, needs review
}

# Helper Functions
def construct_message(m, message_type): 
    """ Prepends message size and type, appends ProtocolType and packs it to binary 
    Args: 
        m (DTCProtocol): DTC protobuf message  
        message_type (int): DTC message type  
    Returns: 
        bytes: Binary string 
    """ 
    total_len = 4 + m.ByteSize()  # 2 bytes Size + 2 bytes Type 
    header = struct.pack('<HH', total_len, message_type)  # Prepare 4-byte little-endian header 
    binary_message = m.SerializeToString() 
    logStdout.info('sending: %s',binary_message)
    logMsg.debug('sending: %s',binary_message)
    return header + binary_message 

def chekker(m):
    for f in m.DESCRIPTOR.fields:
        fmt = f.cpp_type
        if fmt == 8: print('ENUMZZZ: ',f.enum_type.name)
        fv = getattr(m, f.name)
        print(fmt, f.name, fv, type(fv))

def send_message(m, m_type, sock):
    total_len = 4 + m.ByteSize()
    header = struct.pack('HH', total_len, m_type)
    binary_message = m.SerializeToString()
    sock.send(header + binary_message)
    logStdout.info('sending: %s',m_type)
    logMsg.debug('sending: %s',m_type)

def get_message(sock):
    header = sock.recv(4)
    m_size = struct.unpack_from('<H', header[:2])[0]
    m_type = struct.unpack_from('<H', header[2:4])[0]
    m_body = sock.recv(m_size - 4)

    m_type = DTC_MTYPE_MAP[m_type]
    m_resp = m_type[3]()
    m_resp.ParseFromString(m_body)
    logStdout.debug("%s",m_resp)
    return m_type, m_resp

def chekker2(m):
    pktp = tuple(getattr(m,f.name) for f in m.DESCRIPTOR.fields)
    return pktp
    
def quit(sock):
    """ Gracefully logoff and close the connection """
    logStdout.debug("Disconnecting from DTC server")
    logMsg.debug("Disconnecting from DTC server")
    # receiver.stop()
    # heartbeat.stop()
    logoff = Dtc.Logoff()
    logoff.Reason = "Client terminating"
    send_message(logoff, Dtc.LOGOFF, sock)
    # Gracefully close the socket
    sock.close()

# connect+logon and Request Functions
def conn1(addr, encoding=Dtc.PROTOCOL_BUFFERS, heartbeat_interval=10):
    """ Primary function to connect and logon to DTC server""" 
    sock = socket.create_connection(addr)
    # encoding request, construct and send
    enc_req = Dtc.EncodingRequest()
    enc_req.Encoding = encoding
    enc_req.ProtocolType = "DTC"
    enc_req.ProtocolVersion = Dtc.CURRENT_VERSION
    send_message(enc_req, Dtc.ENCODING_REQUEST,sock) # send the encoding request
    # receive encoding response
    m_type, m_resp = get_message(sock)
    logMsg.debug("%s, %s", m_type[0], m_resp)
    logStdout.debug("%s, %s", m_type[0], m_resp)

    # Logon request, construct and send
    logon_req = Dtc.LogonRequest()
    logon_req.ProtocolVersion = Dtc.CURRENT_VERSION
    # logon_req.Username = "wat"
    # logon_req.Password = "wat"
    logon_req.GeneralTextData = "John's Test"
    logon_req.HeartbeatIntervalInSeconds = heartbeat_interval
    logon_req.ClientName = "John_Tester"
    send_message(logon_req, Dtc.LOGON_REQUEST,sock)
    # receive logon response
    m_type, m_resp = get_message(sock)
    logMsg.debug("%s, %s", m_type[0], m_resp)
    logStdout.debug("%s, %s", m_type[0], m_resp)

    return sock

def create_logger(logfile):
    """Create custom logger with own logfile for each DTC Request function"""
    logRec = logging.getLogger('Req')
    logRec.setLevel(logging.DEBUG)
    logRec_handler = logging.FileHandler(logfile)
    fmtRec = logging.Formatter("%(message)s")
    logRec_handler.setFormatter(fmtRec)
    logRec.addHandler(logRec_handler)
    return logRec

def secdef(requestID, symbol, exchange, sock, logfile):
    """ Retrieve Security Definition for each symbol. 
    Uses the Market port"""
    # custom logger with own txt file
    logRec = create_logger(logfile)

    # Create sec def request
    data_req = Dtc.SecurityDefinitionForSymbolRequest()
    data_req.RequestID = requestID  # Note: Make sure this is unique when requesting multiple symbols
    data_req.Symbol = symbol
    data_req.Exchange = exchange
    # Send Request and log response
    send_message(data_req, Dtc.SECURITY_DEFINITION_FOR_SYMBOL_REQUEST,sock)
    m_type, m_resp = get_message(sock)
    logRec.debug("%s, %s", m_type[0], m_resp)
    logStdout.debug("%s, %s", m_type[0], m_resp)
    quit(sock)

def history(requestID, symbol, exchange, record_interval, sock, logfile, start=0, end=0, max=0):
    """Retrieve Historical data direct from DTC"""
    # custom logger with own txt file
    logRec = create_logger(logfile)

    # Create Historical Data Request
    data_req = Dtc.HistoricalPriceDataRequest()
    data_req.RequestID = requestID  # Note: Make sure this is unique when requesting multiple symbols
    data_req.Symbol = symbol
    data_req.Exchange = exchange
    data_req.RecordInterval = record_interval
    data_req.StartDateTime = start
    data_req.EndDateTime = end
    data_req.MaxDaysToReturn = max
    # Send Request and log Response_Header
    send_message(data_req, Dtc.HISTORICAL_PRICE_DATA_REQUEST,sock)
    m_type, m_resp = get_message(sock)
    logRec.debug("%s, %s", m_type[0], m_resp)
    logStdout.debug("%s, %s", m_type[0], m_resp)
    # Get the rest/whole of the historical data
    while True:
        mt, mr = get_message(sock)
        mr1 = chekker2(mr)
        logRec.debug("%s, %s", mt[0], mr1)
        logStdout.debug("%s, %s", mt[0], mr1)
        if mt[0] == 'HISTORICAL_PRICE_DATA_RECORD_RESPONSE' and mr.IsFinalRecord:
            logStdout.info('FINISH')
            break
    quit(sock)
