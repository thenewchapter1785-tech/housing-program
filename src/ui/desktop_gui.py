import os
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from housing_scraper.auth_manager import AuthManager
from housing_scraper.filter_builder import FilterBuilder
from housing_scraper.lister_interface import ListerInterface
from housing_scraper.master_listing_db import MasterListingDatabase
from housing_scraper.role_auth import GovernmentEmailValidator, RoleBasedAuthManager
from housing_scraper.search_manager import SearchManager
from housing_scraper.storage import StorageManager


class DesktopApp:
    def __init__(self) -> None:
        self.storage = StorageManager(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "housing_app"),
        )
        self.storage.ensure_schema()

        self.master_db = MasterListingDatabase(self.storage.connection)
        self.master_db.ensure_schema()

        self.auth_manager = AuthManager(self.storage)
        self.role_auth = RoleBasedAuthManager(self.storage)
        self.role_auth.ensure_role_schema()

        self.current_user: Optional[dict] = None
        self.current_role: str = "searcher"

        self.root = tk.Tk()
        self.root.title("Housing Platform")
        self.root.geometry("1024x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.auth_tab = ttk.Frame(self.notebook)
        self.search_tab = ttk.Frame(self.notebook)
        self.lister_tab = ttk.Frame(self.notebook)
        self.master_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.auth_tab, text="Auth")
        self.notebook.add(self.search_tab, text="Search")
        self.notebook.add(self.lister_tab, text="Lister")
        self.notebook.add(self.master_tab, text="Master DB")

        self._build_auth_tab()
        self._build_search_tab()
        self._build_lister_tab()
        self._build_master_tab()
        self._set_role_visibility()

    def _build_auth_tab(self) -> None:
        frame = ttk.Frame(self.auth_tab, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Email").grid(row=0, column=0, sticky="w")
        self.auth_email = tk.StringVar()
        ttk.Entry(frame, textvariable=self.auth_email, width=40).grid(row=0, column=1, sticky="w")

        ttk.Label(frame, text="Password").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.auth_password = tk.StringVar()
        ttk.Entry(frame, textvariable=self.auth_password, show="*", width=40).grid(
            row=1, column=1, sticky="w", pady=(8, 0)
        )

        ttk.Label(frame, text="Display Name").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.auth_display_name = tk.StringVar()
        ttk.Entry(frame, textvariable=self.auth_display_name, width=40).grid(
            row=2, column=1, sticky="w", pady=(8, 0)
        )

        ttk.Label(frame, text="Role").grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.auth_role = tk.StringVar(value="searcher")
        role_combo = ttk.Combobox(
            frame,
            textvariable=self.auth_role,
            values=["searcher", "lister"],
            state="readonly",
            width=20,
        )
        role_combo.grid(row=3, column=1, sticky="w", pady=(8, 0))

        button_row = ttk.Frame(frame)
        button_row.grid(row=4, column=0, columnspan=2, sticky="w", pady=(16, 0))

        ttk.Button(button_row, text="Register", command=self.register_user).pack(side="left", padx=(0, 8))
        ttk.Button(button_row, text="Login", command=self.login_user).pack(side="left", padx=(0, 8))
        ttk.Button(button_row, text="Logout", command=self.logout_user).pack(side="left")

        self.auth_status = tk.StringVar(value="Not logged in")
        ttk.Label(frame, textvariable=self.auth_status).grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(16, 0)
        )

    def _build_search_tab(self) -> None:
        frame = ttk.Frame(self.search_tab, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Location").grid(row=0, column=0, sticky="w")
        self.search_location = tk.StringVar(value="Seattle")
        ttk.Entry(frame, textvariable=self.search_location, width=30).grid(row=0, column=1, sticky="w")

        ttk.Label(frame, text="Query").grid(row=0, column=2, sticky="w", padx=(16, 0))
        self.search_query = tk.StringVar(value="1 bedroom")
        ttk.Entry(frame, textvariable=self.search_query, width=30).grid(row=0, column=3, sticky="w")

        self.voucher_only = tk.BooleanVar(value=False)
        self.record_only = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Voucher-friendly only", variable=self.voucher_only).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )
        ttk.Checkbutton(frame, text="Record-friendly only", variable=self.record_only).grid(
            row=1, column=2, columnspan=2, sticky="w", pady=(8, 0)
        )

        ttk.Button(frame, text="Run Search", command=self.run_search).grid(
            row=2, column=0, sticky="w", pady=(12, 0)
        )

        self.search_results = tk.Text(frame, wrap="word", height=28)
        self.search_results.grid(row=3, column=0, columnspan=4, sticky="nsew", pady=(12, 0))

        frame.rowconfigure(3, weight=1)
        frame.columnconfigure(3, weight=1)

    def _build_lister_tab(self) -> None:
        frame = ttk.Frame(self.lister_tab, padding=16)
        frame.pack(fill="both", expand=True)

        self.list_title = tk.StringVar()
        self.list_location = tk.StringVar(value="Seattle")
        self.list_price = tk.StringVar()
        self.list_contact_name = tk.StringVar()
        self.list_contact_phone = tk.StringVar()
        self.list_contact_email = tk.StringVar()
        self.list_description = tk.StringVar()
        self.list_voucher = tk.BooleanVar(value=False)
        self.list_record = tk.BooleanVar(value=False)

        labels = [
            ("Title", self.list_title),
            ("Location", self.list_location),
            ("Price", self.list_price),
            ("Contact Name", self.list_contact_name),
            ("Contact Phone", self.list_contact_phone),
            ("Contact Email", self.list_contact_email),
            ("Description", self.list_description),
        ]

        for idx, (label, var) in enumerate(labels):
            ttk.Label(frame, text=label).grid(row=idx, column=0, sticky="w")
            ttk.Entry(frame, textvariable=var, width=60).grid(row=idx, column=1, sticky="w", pady=4)

        ttk.Checkbutton(frame, text="Voucher-friendly", variable=self.list_voucher).grid(
            row=7, column=0, sticky="w", pady=(8, 0)
        )
        ttk.Checkbutton(frame, text="Record-friendly", variable=self.list_record).grid(
            row=7, column=1, sticky="w", pady=(8, 0)
        )

        ttk.Button(frame, text="Add Listing", command=self.add_listing).grid(
            row=8, column=0, sticky="w", pady=(12, 0)
        )

        self.lister_status = tk.StringVar(value="Lister actions require lister role login")
        ttk.Label(frame, textvariable=self.lister_status).grid(
            row=9, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )

    def _build_master_tab(self) -> None:
        frame = ttk.Frame(self.master_tab, padding=16)
        frame.pack(fill="both", expand=True)

        self.master_location = tk.StringVar(value="Seattle")
        ttk.Label(frame, text="Location").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.master_location, width=30).grid(row=0, column=1, sticky="w")
        ttk.Button(frame, text="Load Master Listings", command=self.load_master_listings).grid(
            row=0, column=2, sticky="w", padx=(12, 0)
        )

        self.master_results = tk.Text(frame, wrap="word", height=30)
        self.master_results.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(12, 0))

        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)

    def _set_role_visibility(self) -> None:
        if self.current_user is None:
            self.notebook.tab(1, state="disabled")
            self.notebook.tab(2, state="disabled")
            self.notebook.tab(3, state="disabled")
            return

        self.notebook.tab(1, state="normal")
        self.notebook.tab(3, state="normal")
        if self.current_role == "lister":
            self.notebook.tab(2, state="normal")
        else:
            self.notebook.tab(2, state="disabled")

    def register_user(self) -> None:
        email = self.auth_email.get().strip()
        password = self.auth_password.get().strip()
        display_name = self.auth_display_name.get().strip() or None
        role = self.auth_role.get().strip()

        if not email or not password:
            messagebox.showerror("Validation", "Email and password are required.")
            return

        if role == "lister":
            is_gov, _ = GovernmentEmailValidator.is_government_email(email)
            if not is_gov:
                messagebox.showerror("Access denied", "Lister accounts require .gov email.")
                return
            GovernmentEmailValidator.whitelist_email(self.storage, email)

        success, message, user = self.role_auth.register_with_role(
            email=email,
            password=password,
            display_name=display_name,
            role=role,
        )
        if not success or not user:
            messagebox.showerror("Registration failed", message)
            return

        self.current_user = user
        self.current_role = role
        self.auth_manager.session_manager.create_session(user)
        self.auth_status.set(f"Logged in as {user['email']} ({role})")
        self._set_role_visibility()
        messagebox.showinfo("Success", message)

    def login_user(self) -> None:
        email = self.auth_email.get().strip()
        password = self.auth_password.get().strip()
        if not email or not password:
            messagebox.showerror("Validation", "Email and password are required.")
            return

        success, message, user = self.auth_manager.login_with_validation(email, password)
        if not success or not user:
            messagebox.showerror("Login failed", message)
            return

        self.current_user = user
        self.current_role = self.role_auth.get_user_role(int(user["id"])) or "searcher"
        self.auth_status.set(f"Logged in as {user['email']} ({self.current_role})")
        self._set_role_visibility()
        messagebox.showinfo("Success", message)

    def logout_user(self) -> None:
        if self.current_user is not None:
            self.auth_manager.logout(int(self.current_user["id"]))
        self.current_user = None
        self.current_role = "searcher"
        self.auth_status.set("Not logged in")
        self._set_role_visibility()

    def run_search(self) -> None:
        if not self.current_user:
            messagebox.showerror("Auth", "Please login first.")
            return

        search_mgr = SearchManager(self.storage, master_db=self.master_db)
        search_mgr.set_user(self.current_user)

        filter_builder = FilterBuilder()
        filter_builder.voucher_accepted = True if self.voucher_only.get() else None
        filter_builder.record_friendly = True if self.record_only.get() else None

        result = search_mgr.run_search(
            location=self.search_location.get().strip() or "Seattle",
            query=self.search_query.get().strip() or "apartment",
            providers=["craigslist", "rentals", "padmapper", "rightmove"],
            filter_builder=filter_builder,
        )

        lines = [
            f"Search #{result['search_id']} - {result['location']} / {result['query']}",
            f"Total: {len(result['results'])}",
            "",
        ]
        for listing in result["results"]:
            lines.append(f"- {listing.title} | {listing.source} | {listing.price}")

        self.search_results.delete("1.0", tk.END)
        self.search_results.insert(tk.END, "\n".join(lines))

    def add_listing(self) -> None:
        if not self.current_user or self.current_role != "lister":
            messagebox.showerror("Access denied", "Only lister accounts can add listings.")
            return

        lister = ListerInterface(int(self.current_user["id"]), self.storage, self.master_db)
        success, message, listing_id = lister.add_property(
            title=self.list_title.get().strip(),
            location=self.list_location.get().strip(),
            price=self.list_price.get().strip() or None,
            description=self.list_description.get().strip() or None,
            contact_name=self.list_contact_name.get().strip() or None,
            contact_phone=self.list_contact_phone.get().strip() or None,
            contact_email=self.list_contact_email.get().strip() or None,
            voucher_friendly=self.list_voucher.get(),
            record_friendly=self.list_record.get(),
        )

        if not success:
            messagebox.showerror("Add listing failed", message)
            return

        self.lister_status.set(f"Listing added successfully (ID: {listing_id})")
        messagebox.showinfo("Success", message)

    def load_master_listings(self) -> None:
        listings = self.master_db.get_listings_by_location(
            self.master_location.get().strip() or "Seattle"
        )

        self.master_results.delete("1.0", tk.END)
        if not listings:
            self.master_results.insert(tk.END, "No listings found.")
            return

        text = []
        for listing in listings:
            text.append(
                f"[{listing['id']}] {listing['title']} | {listing.get('price')} | {listing.get('location')}"
            )
        self.master_results.insert(tk.END, "\n".join(text))

    def on_close(self) -> None:
        self.storage.close()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()
