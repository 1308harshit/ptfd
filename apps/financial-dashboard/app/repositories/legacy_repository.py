"""Repository for legacy database operations."""
import contextlib
from typing import Optional, Dict, Any, List, Tuple, Union
import logging

from sqlalchemy import create_engine, MetaData, Table, text, select, update, inspect
from sqlalchemy.engine import URL, Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


class DatabaseConfig:
    """Configuration for database connection."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 33060,
        user: str = "root",
        password: str = "root",
        database: str = "smw_legacy_full",
        connect_timeout: int = 10
    ):
        """Initialize database configuration.
        
        Args:
            host: Database host
            port: Database port
            user: Database user
            password: Database password
            database: Database name
            connect_timeout: Connection timeout in seconds
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connect_timeout = connect_timeout
        
    def get_connection_url(self) -> URL:
        """Get SQLAlchemy connection URL."""
        return URL.create(
            "mysql+mysqlconnector",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
            query={"connect_timeout": str(self.connect_timeout)}
        )


class LegacyDatabaseRepository:
    """Base repository for accessing legacy database using dynamic reflection."""
    
    def __init__(self, config: DatabaseConfig):
        """Initialize repository with database configuration."""
        self.config = config
        self._engine = None
        self._metadata = None
        self._tables = {}
        self.logger = logging.getLogger(__name__)
        
    @property
    def engine(self) -> Engine:
        """Get or create the SQLAlchemy engine."""
        if self._engine is None:
            self._engine = create_engine(
                self.config.get_connection_url(),
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
        return self._engine
        
    @property
    def metadata(self) -> MetaData:
        """Get or create the SQLAlchemy metadata."""
        if self._metadata is None:
            self._metadata = MetaData()
        return self._metadata
        
    def get_table(self, table_name: str) -> Table:
        """Get a reflected table by name."""
        if table_name not in self._tables:
            self._tables[table_name] = Table(
                table_name, self.metadata, autoload_with=self.engine
            )
        return self._tables[table_name]
    
    @contextlib.contextmanager
    def session(self):
        """Context manager to create a SQLAlchemy session."""
        session = Session(self.engine)
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
            
    @contextlib.contextmanager
    def connection(self):
        """Context manager to create a SQLAlchemy connection."""
        connection = self.engine.connect()
        try:
            yield connection
        except SQLAlchemyError as e:
            self.logger.error(f"Database connection error: {e}")
            raise
        finally:
            connection.close()
            
    @contextlib.contextmanager
    def check_database_connection(self) -> bool:
        """Check if the database connection is working."""
        try:
            with self.session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            return False
            
    # --------------------------- Financial Dashboard Queries ---------------------------
    
    def get_customers_with_misapplied_payments(self) -> List[Dict[str, Any]]:
        """
        Find customers who have payments that were potentially misapplied.
        
        This uses a heuristic to identify suspicious payment patterns, where a payment
        was applied to a future lesson when past lessons remain unpaid.
        """
        query = """
        SELECT DISTINCT 
            p.user_id, 
            up.firstname, 
            up.lastname, 
            COUNT(DISTINCT p.id) as num_suspicious_payments
        FROM 
            payment p
            JOIN lesson_payment lp ON p.id = lp.paymentId
            JOIN lesson l_paid ON lp.lessonId = l_paid.id
            JOIN enrolment e ON l_paid.courseId = e.courseId 
            JOIN student s ON e.studentId = s.id
            JOIN user_profile up ON p.user_id = up.user_id
        WHERE 
            s.customer_id = p.user_id
            AND EXISTS (
                SELECT 1
                FROM lesson l_unpaid
                JOIN enrolment e_unpaid ON l_unpaid.courseId = e_unpaid.courseId 
                JOIN student s_unpaid ON e_unpaid.studentId = s_unpaid.id
                WHERE 
                    s_unpaid.customer_id = p.user_id
                    AND l_unpaid.paidStatus = 0
                    AND l_unpaid.date < l_paid.date
                    AND l_unpaid.dueDate <= l_paid.date
                    AND DATEDIFF(l_paid.date, l_unpaid.date) > 14
                    AND l_paid.date > p.date
            )
        GROUP BY 
            p.user_id, 
            up.firstname, 
            up.lastname
        ORDER BY 
            num_suspicious_payments DESC
        LIMIT 100
        """
        
        result = []
        try:
            with self.session() as session:
                rows = session.execute(text(query)).fetchall()
                for row in rows:
                    result.append(dict(row))
        except Exception as e:
            self.logger.error(f"Error finding customers with misapplied payments: {e}")
        
        return result
        
    def get_customer_details(self, customer_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a customer.
        
        Args:
            customer_id: The ID of the customer
            
        Returns:
            Dictionary with customer details
        """
        query = """
        SELECT 
            u.id as user_id,
            CONCAT(up.firstname, ' ', up.lastname) as customer_name,
            ue.email,
            ca.balance,
            (
                SELECT pf.name
                FROM enrolment e 
                JOIN payment_frequency pf ON e.paymentFrequencyId = pf.id
                JOIN student s ON e.studentId = s.id
                WHERE s.customer_id = u.id
                GROUP BY pf.name
                ORDER BY COUNT(*) DESC
                LIMIT 1
            ) as payment_frequency
        FROM 
            user u
            JOIN user_profile up ON u.id = up.user_id
            LEFT JOIN user_email ue ON u.id = ue.user_id
            LEFT JOIN customer_account ca ON u.id = ca.user_id
        WHERE 
            u.id = :customer_id
        LIMIT 1
        """
        
        try:
            with self.session() as session:
                row = session.execute(text(query), {"customer_id": customer_id}).fetchone()
                if row:
                    return dict(row)
        except Exception as e:
            self.logger.error(f"Error getting customer details: {e}")
        
        return {}
        
    def get_customer_payments(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get all payments for a customer.
        
        Args:
            customer_id: The ID of the customer
            
        Returns:
            List of payment records
        """
        query = """
        SELECT 
            p.id as payment_id,
            p.date as payment_date,
            p.amount,
            p.balance,
            p.status,
            pm.name as payment_method
        FROM 
            payment p
            LEFT JOIN payment_method pm ON p.payment_method_id = pm.id
        WHERE 
            p.user_id = :customer_id
        ORDER BY 
            p.date DESC
        LIMIT 100
        """
        
        result = []
        try:
            with self.session() as session:
                rows = session.execute(text(query), {"customer_id": customer_id}).fetchall()
                for row in rows:
                    result.append(dict(row))
        except Exception as e:
            self.logger.error(f"Error getting customer payments: {e}")
        
        return result
        
    def get_payment_details(self, payment_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a payment.
        
        Args:
            payment_id: The ID of the payment
            
        Returns:
            Dictionary with payment details
        """
        query = """
        SELECT 
            p.id as payment_id,
            p.user_id,
            p.date as payment_date,
            p.amount,
            p.balance,
            p.status,
            pm.name as payment_method,
            CONCAT(up.firstname, ' ', up.lastname) as customer_name
        FROM 
            payment p
            LEFT JOIN payment_method pm ON p.payment_method_id = pm.id
            LEFT JOIN user_profile up ON p.user_id = up.user_id
        WHERE 
            p.id = :payment_id
        LIMIT 1
        """
        
        try:
            with self.session() as session:
                row = session.execute(text(query), {"payment_id": payment_id}).fetchone()
                if row:
                    return dict(row)
        except Exception as e:
            self.logger.error(f"Error getting payment details: {e}")
        
        return {}
        
    def get_related_enrolment_details(self, payment_id: str) -> Dict[str, Any]:
        """
        Get details about enrollments related to a payment.
        
        Args:
            payment_id: The ID of the payment
            
        Returns:
            Dictionary with enrollment details
        """
        query = """
        SELECT 
            e.id as enrolment_id,
            e.paymentFrequencyId,
            pf.name as payment_frequency,
            e.startDateTime,
            e.endDateTime,
            e.isAutoRenew,
            s.first_name as student_first_name,
            s.last_name as student_last_name,
            s.id as student_id,
            c.name as course_name
        FROM 
            lesson_payment lp
            JOIN lesson l ON lp.lessonId = l.id
            JOIN enrolment e ON lp.enrolmentId = e.id
            JOIN student s ON e.studentId = s.id
            JOIN course c ON e.courseId = c.id
            JOIN payment_frequency pf ON e.paymentFrequencyId = pf.id
        WHERE 
            lp.paymentId = :payment_id
        GROUP BY 
            e.id
        LIMIT 1
        """
        
        try:
            with self.session() as session:
                row = session.execute(text(query), {"payment_id": payment_id}).fetchone()
                if row:
                    return dict(row)
        except Exception as e:
            self.logger.error(f"Error getting related enrollment details: {e}")
        
        return {}
        
    def get_current_payment_applications(self, payment_id: str) -> List[Dict[str, Any]]:
        """
        Get current applications of a payment to lessons.
        
        Args:
            payment_id: The ID of the payment
            
        Returns:
            List of lesson payment applications
        """
        query = """
        SELECT 
            l.id as lesson_id,
            l.date as lesson_date,
            l.dueDate as lesson_due_date,
            l.total as lesson_amount,
            lp.amount as applied_amount,
            e.id as enrolment_id,
            s.first_name as student_first_name,
            s.last_name as student_last_name,
            s.id as student_id,
            p.date as payment_date,
            CASE WHEN l.date > p.date THEN 1 ELSE 0 END as is_future_lesson
        FROM 
            lesson_payment lp
            JOIN lesson l ON lp.lessonId = l.id
            JOIN enrolment e ON lp.enrolmentId = e.id
            JOIN student s ON e.studentId = s.id
            JOIN payment p ON lp.paymentId = p.id
        WHERE 
            lp.paymentId = :payment_id
        ORDER BY 
            l.date
        """
        
        result = []
        try:
            with self.session() as session:
                rows = session.execute(text(query), {"payment_id": payment_id}).fetchall()
                for row in rows:
                    result.append(dict(row))
        except Exception as e:
            self.logger.error(f"Error getting current payment applications: {e}")
        
        return result
        
    def get_affected_enrollments(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get enrollments potentially affected by issues, such as expired but not auto-renewed.
        
        Args:
            start_date: Start date for analysis period
            end_date: End date for analysis period
            
        Returns:
            List of potentially affected enrollments
        """
        query = """
        SELECT 
            e.id as enrolment_id,
            s.first_name,
            s.last_name,
            s.customer_id,
            e.endDateTime,
            e.isAutoRenew,
            c.name as course_name
        FROM 
            enrolment e
            JOIN student s ON e.studentId = s.id
            JOIN course c ON e.courseId = c.id
        WHERE 
            e.endDateTime <= :end_date
            AND e.isAutoRenew = 0
            AND EXISTS (
                SELECT 1 
                FROM lesson l 
                WHERE 
                    l.courseId = e.courseId 
                    AND l.date > :end_date 
                    AND l.status != 2  -- Status 2 is typically CANCELLED
            )
        ORDER BY 
            e.endDateTime
        LIMIT 100
        """
        
        result = []
        try:
            with self.session() as session:
                rows = session.execute(
                    text(query), 
                    {"start_date": start_date, "end_date": end_date}
                ).fetchall()
                for row in rows:
                    result.append(dict(row))
        except Exception as e:
            self.logger.error(f"Error getting affected enrollments: {e}")
        
        return result
        
    def get_customer_enrollments(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get all enrollments for a customer's students.
        
        Args:
            customer_id: The ID of the customer
            
        Returns:
            List of enrollment records
        """
        query = """
        SELECT 
            e.id as enrolment_id,
            CONCAT(s.first_name, ' ', s.last_name) as student_name,
            c.name as course_name,
            pf.name as payment_frequency,
            e.startDateTime,
            e.endDateTime,
            e.isAutoRenew
        FROM 
            enrolment e
            JOIN student s ON e.studentId = s.id
            JOIN course c ON e.courseId = c.id
            JOIN payment_frequency pf ON e.paymentFrequencyId = pf.id
        WHERE 
            s.customer_id = :customer_id
        ORDER BY 
            e.startDateTime DESC
        LIMIT 100
        """
        
        result = []
        try:
            with self.session() as session:
                rows = session.execute(text(query), {"customer_id": customer_id}).fetchall()
                for row in rows:
                    result.append(dict(row))
        except Exception as e:
            self.logger.error(f"Error getting customer enrollments: {e}")
        
        return result
        
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to the database and return version info."""
        try:
            with self.connection() as conn:
                result = conn.execute(text("SELECT VERSION() as version"))
                row = result.fetchone()
                return {"connected": True, "version": row[0] if row else None}
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return {"connected": False, "error": str(e)}
            
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a raw SQL query and return results as dictionaries."""
        try:
            with self.connection() as conn:
                result = conn.execute(text(query), params or {})
                return [dict(row) for row in result.mappings()]
        except Exception as e:
            self.logger.error(f"Query execution error: {e}")
            self.logger.error(f"Query: {query}")
            self.logger.error(f"Params: {params}")
            raise

    def fetch_payment_data(self, limit: int = 1000, customer_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch payment data for analysis dashboards."""
        query = """
        SELECT 
            p.id as payment_id,
            p.amount,
            p.created_at as payment_date,
            p.status,
            p.payment_method,
            a.id as account_id,
            CONCAT(c.first_name, ' ', c.last_name) as customer_name,
            i.id as invoice_id,
            i.amount as invoice_amount,
            i.created_at as invoice_date,
            l.id as lesson_id,
            l.date as lesson_date,
            l.status as lesson_status,
            e.id as enrollment_id,
            c.id as customer_id
        FROM 
            payment p
        LEFT JOIN 
            account a ON p.account_id = a.id
        LEFT JOIN 
            customer c ON a.customer_id = c.id
        LEFT JOIN 
            payment_invoice pi ON p.id = pi.payment_id
        LEFT JOIN 
            invoice i ON pi.invoice_id = i.id
        LEFT JOIN 
            invoice_lesson il ON i.id = il.invoice_id
        LEFT JOIN 
            lesson l ON il.lesson_id = l.id
        LEFT JOIN 
            enrollment e ON l.enrollment_id = e.id
        WHERE 
            p.deleted_at IS NULL
        """
        params = {"limit": limit}
        
        # Add customer_id filter if provided
        if customer_id:
            query += " AND c.id = :customer_id"
            params["customer_id"] = customer_id
            
        query += """
        ORDER BY 
            p.created_at DESC
        LIMIT :limit
        """
        
        try:
            return self.execute_query(query, params)
        except Exception:
            self.logger.error("Failed to fetch payment data")
            return []
            
    def fetch_payment_cycle_data(self) -> List[Dict[str, Any]]:
        """Fetch payment data with billing cycle information."""
        query = """
        SELECT 
            p.id as payment_id,
            p.amount,
            p.created_at as payment_date,
            YEAR(p.created_at) * 100 + MONTH(p.created_at) as payment_yearmonth,
            a.id as account_id,
            i.id as invoice_id,
            i.created_at as invoice_date,
            YEAR(i.created_at) * 100 + MONTH(i.created_at) as invoice_yearmonth,
            DATEDIFF(i.created_at, p.created_at) as days_difference,
            pi.amount as applied_amount,
            e.billing_cycle_day
        FROM 
            payment p
        JOIN 
            account a ON p.account_id = a.id
        JOIN 
            payment_invoice pi ON p.id = pi.payment_id
        JOIN 
            invoice i ON pi.invoice_id = i.id
        LEFT JOIN 
            invoice_lesson il ON i.id = il.invoice_id
        LEFT JOIN 
            lesson l ON il.lesson_id = l.id
        LEFT JOIN 
            enrollment e ON l.enrollment_id = e.id
        WHERE 
            p.deleted_at IS NULL
            AND i.deleted_at IS NULL
        ORDER BY 
            p.created_at DESC
        LIMIT 5000
        """
        try:
            return self.execute_query(query)
        except Exception:
            self.logger.error("Failed to fetch payment cycle data")
            return []
            
    def fetch_misapplied_payments(self) -> List[Dict[str, Any]]:
        """Fetch potentially misapplied payments (payment date after invoice date)."""
        query = """
        SELECT 
            p.id as payment_id,
            p.amount as payment_amount,
            p.created_at as payment_date,
            YEAR(p.created_at) * 100 + MONTH(p.created_at) as payment_yearmonth,
            a.id as account_id,
            CONCAT(c.first_name, ' ', c.last_name) as customer_name,
            i.id as invoice_id,
            i.created_at as invoice_date,
            YEAR(i.created_at) * 100 + MONTH(i.created_at) as invoice_yearmonth,
            pi.amount as applied_amount,
            DATEDIFF(p.created_at, i.created_at) as days_difference,
            e.billing_cycle_day
        FROM 
            payment p
        JOIN 
            account a ON p.account_id = a.id
        JOIN 
            customer c ON a.customer_id = c.id
        JOIN 
            payment_invoice pi ON p.id = pi.payment_id
        JOIN 
            invoice i ON pi.invoice_id = i.id
        LEFT JOIN 
            invoice_lesson il ON i.id = il.invoice_id
        LEFT JOIN 
            lesson l ON il.lesson_id = l.id
        LEFT JOIN 
            enrollment e ON l.enrollment_id = e.id
        WHERE 
            p.deleted_at IS NULL
            AND i.deleted_at IS NULL
            AND p.created_at > i.created_at
            AND DATEDIFF(p.created_at, i.created_at) > 15
        ORDER BY 
            days_difference DESC
        LIMIT 5000
        """
        try:
            return self.execute_query(query)
        except Exception:
            self.logger.error("Failed to fetch misapplied payments")
            return []

    def fetch_enrolment_data(self, customer_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch enrolment data for a customer."""
        query = """
        SELECT 
            e.id as enrolment_id,
            e.created_at as enrolment_date,
            p.id as program_id,
            p.name as program_name,
            c.id as customer_id,
            CONCAT(c.first_name, ' ', c.last_name) as customer_name
        FROM 
            enrollment e
        JOIN 
            program p ON e.program_id = p.id
        JOIN 
            customer c ON e.customer_id = c.id
        WHERE 
            e.deleted_at IS NULL
        """
        params = {}
        
        if customer_id:
            query += " AND c.id = :customer_id"
            params["customer_id"] = customer_id
            
        query += " ORDER BY e.created_at DESC LIMIT 1000"
        
        try:
            return self.execute_query(query, params)
        except Exception:
            self.logger.error("Failed to fetch enrolment data")
            return []
            
    def fetch_lesson_data(self, customer_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch lesson data for a customer."""
        query = """
        SELECT 
            l.id as lesson_id,
            l.date as lesson_date,
            l.status as lesson_status,
            CASE 
                WHEN l.group_id IS NULL THEN 'Private'
                ELSE 'Group'
            END as lesson_type,
            e.id as enrolment_id,
            c.id as customer_id,
            CONCAT(c.first_name, ' ', c.last_name) as customer_name
        FROM 
            lesson l
        JOIN 
            enrollment e ON l.enrollment_id = e.id
        JOIN 
            customer c ON e.customer_id = c.id
        WHERE 
            l.deleted_at IS NULL
        """
        params = {}
        
        if customer_id:
            query += " AND c.id = :customer_id"
            params["customer_id"] = customer_id
            
        query += " ORDER BY l.date DESC LIMIT 1000"
        
        try:
            return self.execute_query(query, params)
        except Exception:
            self.logger.error("Failed to fetch lesson data")
            return []
            
    def fetch_invoice_data(self, customer_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch invoice data for a customer."""
        query = """
        SELECT 
            i.id as invoice_id,
            i.created_at as invoice_date,
            i.amount,
            i.status,
            a.id as account_id,
            c.id as customer_id,
            CONCAT(c.first_name, ' ', c.last_name) as customer_name,
            il.lesson_id
        FROM 
            invoice i
        JOIN 
            account a ON i.account_id = a.id
        JOIN 
            customer c ON a.customer_id = c.id
        LEFT JOIN 
            invoice_lesson il ON i.id = il.invoice_id
        WHERE 
            i.deleted_at IS NULL
        """
        params = {}
        
        if customer_id:
            query += " AND c.id = :customer_id"
            params["customer_id"] = customer_id
            
        query += " ORDER BY i.created_at DESC LIMIT 1000"
        
        try:
            return self.execute_query(query, params)
        except Exception:
            self.logger.error("Failed to fetch invoice data")
            return []
